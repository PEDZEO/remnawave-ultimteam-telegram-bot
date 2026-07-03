import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, time as datetime_time, timedelta
from html import escape
from zoneinfo import ZoneInfo

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import func, select

from app.config import settings
from app.database.database import AsyncSessionLocal
from app.database.models import TapRewardDailyStats, User


logger = structlog.get_logger(__name__)


class TapRewardReportServiceError(RuntimeError):
    """Base error for tap reward reporting."""


@dataclass(slots=True)
class TapRewardUserDailyRow:
    user: User
    stats: TapRewardDailyStats


@dataclass(slots=True)
class TapRewardDailyReportData:
    report_date: date
    active_users: int
    total_taps: int
    total_rewards: int
    balance_reward_kopeks: int
    subscription_reward_days: int
    top_rows: list[TapRewardUserDailyRow]


class TapRewardReportService:
    def __init__(self) -> None:
        self.bot: Bot | None = None
        self._task: asyncio.Task | None = None
        self._moscow_tz = ZoneInfo('Europe/Moscow')

    def set_bot(self, bot: Bot) -> None:
        self.bot = bot

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        await self.stop()

        if not settings.TAP_REWARDS_DAILY_REPORT_ENABLED:
            logger.info('Tap reward daily report service is disabled by settings')
            return

        if not self.bot:
            logger.warning('Cannot start tap reward daily report service without bot')
            return

        if not self._chat_id():
            logger.warning('Tap reward daily report service is not started: admin/report chat is not configured')
            return

        send_time = self._send_time()
        if not send_time:
            logger.warning('Tap reward daily report service is not started: send time is invalid')
            return

        self._task = asyncio.create_task(self._auto_daily_loop(send_time))
        logger.info('Tap reward daily report service started', send_time=send_time.strftime('%H:%M'))

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def send_daily_report(
        self,
        report_date: date | None = None,
        *,
        send_to_topic: bool = False,
    ) -> str:
        target_date = report_date or (datetime.now(self._moscow_tz).date() - timedelta(days=1))
        report_text = await self._build_daily_report(target_date)

        if send_to_topic:
            await self._deliver_report(report_text)

        return report_text

    async def _auto_daily_loop(self, send_time: datetime_time) -> None:
        try:
            next_run_utc, report_date = self._calculate_next_run(send_time)

            while True:
                delay = (next_run_utc - datetime.now(UTC)).total_seconds()
                if delay > 0:
                    await asyncio.sleep(delay)

                try:
                    await self.send_daily_report(report_date, send_to_topic=True)
                    logger.info('Tap reward daily report sent', report_date=report_date.strftime('%d.%m.%Y'))
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.error('Failed to send tap reward daily report', report_date=report_date, error=error)

                next_run_utc, report_date = self._calculate_next_run(send_time)

        except asyncio.CancelledError:
            logger.info('Tap reward daily report service stopped')
            raise
        except Exception as error:
            logger.error('Critical tap reward daily report service error', error=error)

    def _calculate_next_run(self, send_time: datetime_time) -> tuple[datetime, date]:
        now_msk = datetime.now(self._moscow_tz)
        candidate = datetime.combine(now_msk.date(), send_time, tzinfo=self._moscow_tz)
        if now_msk >= candidate:
            candidate += timedelta(days=1)

        report_date = (candidate - timedelta(days=1)).date()
        return candidate.astimezone(UTC), report_date

    async def _deliver_report(self, report_text: str) -> None:
        if not self.bot:
            raise TapRewardReportServiceError('Bot is not initialized for tap reward reports')

        chat_id = self._chat_id()
        if not chat_id:
            raise TapRewardReportServiceError('Tap reward report chat is not configured')

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=report_text,
                message_thread_id=self._topic_id(),
                parse_mode='HTML',
                disable_web_page_preview=True,
            )
        except (TelegramBadRequest, TelegramForbiddenError) as error:
            logger.error('Failed to deliver tap reward daily report', error=error)
            raise TapRewardReportServiceError('Failed to deliver tap reward daily report') from error

    async def _build_daily_report(self, report_date: date) -> str:
        data = await self._collect_daily_report_data(report_date)
        lines = [
            f'📊 <b>Тапы за {data.report_date.strftime("%d.%m.%Y")}</b>',
            '',
            '🧭 <b>Итог</b>',
            f'• Пользователей тапало: <b>{data.active_users}</b>',
            f'• Всего тапов: <b>{data.total_taps}</b>',
            f'• Подарков выдано: <b>{data.total_rewards}</b>',
            f'• Балансом выдано: <b>{self._format_rubles(data.balance_reward_kopeks)}</b>',
            f'• Днями подписки: <b>{data.subscription_reward_days} дн.</b>',
            '',
            '👆 <b>Кто сколько тапал</b>',
        ]

        if not data.top_rows:
            lines.append('Тапов за день не было.')
            return '\n'.join(lines)

        for index, row in enumerate(data.top_rows, start=1):
            taps = max(0, int(row.stats.tap_count or 0))
            rewards = max(0, int(row.stats.reward_count or 0))
            reward_tail = f', {rewards} подарков' if rewards else ''
            lines.append(f'{index}. {self._format_user_label(row.user)}: <b>{taps}</b> тапов{reward_tail}')

        return '\n'.join(lines)

    async def _collect_daily_report_data(self, report_date: date) -> TapRewardDailyReportData:
        async with AsyncSessionLocal() as session:
            totals_result = await session.execute(
                select(
                    func.count(TapRewardDailyStats.id),
                    func.coalesce(func.sum(TapRewardDailyStats.tap_count), 0),
                    func.coalesce(func.sum(TapRewardDailyStats.reward_count), 0),
                    func.coalesce(func.sum(TapRewardDailyStats.balance_reward_kopeks), 0),
                    func.coalesce(func.sum(TapRewardDailyStats.subscription_reward_days), 0),
                ).where(TapRewardDailyStats.stat_date == report_date)
            )
            active_users, total_taps, total_rewards, balance_reward_kopeks, subscription_reward_days = totals_result.one()

            top_result = await session.execute(
                select(TapRewardDailyStats, User)
                .join(User, User.id == TapRewardDailyStats.user_id)
                .where(TapRewardDailyStats.stat_date == report_date)
                .order_by(
                    TapRewardDailyStats.tap_count.desc(),
                    TapRewardDailyStats.reward_count.desc(),
                    TapRewardDailyStats.id.asc(),
                )
                .limit(self._top_limit())
            )

            top_rows = [TapRewardUserDailyRow(user=user, stats=stats) for stats, user in top_result.all()]

        return TapRewardDailyReportData(
            report_date=report_date,
            active_users=int(active_users or 0),
            total_taps=int(total_taps or 0),
            total_rewards=int(total_rewards or 0),
            balance_reward_kopeks=int(balance_reward_kopeks or 0),
            subscription_reward_days=int(subscription_reward_days or 0),
            top_rows=top_rows,
        )

    @staticmethod
    def _chat_id() -> int | str | None:
        return settings.get_reports_chat_id() or settings.ADMIN_NOTIFICATIONS_CHAT_ID

    @staticmethod
    def _topic_id() -> int | None:
        return settings.get_reports_topic_id() or settings.ADMIN_NOTIFICATIONS_TOPIC_ID

    @staticmethod
    def _top_limit() -> int:
        try:
            return max(1, int(settings.TAP_REWARDS_DAILY_REPORT_TOP_LIMIT or 10))
        except (TypeError, ValueError):
            return 10

    @staticmethod
    def _send_time() -> datetime_time | None:
        raw_value = str(settings.TAP_REWARDS_DAILY_REPORT_TIME or '').strip()
        try:
            hour_text, minute_text = raw_value.split(':', 1)
            return datetime_time(hour=int(hour_text), minute=int(minute_text))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_user_label(user: User) -> str:
        parts = [f'ID {getattr(user, "id", "unknown")}']
        telegram_id = getattr(user, 'telegram_id', None)
        username = getattr(user, 'username', None)
        email = getattr(user, 'email', None)

        if telegram_id:
            parts.append(f'TG {telegram_id}')
        if username:
            username_text = str(username)
            parts.append(username_text if username_text.startswith('@') else f'@{username_text}')
        if email:
            parts.append(str(email))

        return escape(' / '.join(parts))

    @staticmethod
    def _format_rubles(kopeks: int) -> str:
        rubles = max(0, int(kopeks or 0)) / 100
        if rubles.is_integer():
            return f'{int(rubles)} ₽'
        return f'{rubles:.2f} ₽'


tap_reward_report_service = TapRewardReportService()
