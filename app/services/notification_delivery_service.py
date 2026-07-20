"""
Unified notification delivery service for all user types.

This service delivers notifications independently through every available channel:
- Telegram Bot for users with telegram_id
- Email for users with a verified address
- WebSocket for cabinet users with an active connection
"""

import asyncio
from enum import Enum
from typing import Any

import structlog
from aiogram import Bot

from app.config import settings
from app.database.models import User, UserStatus
from app.utils.ultima_notifications import strip_bot_menu_buttons_for_ultima


logger = structlog.get_logger(__name__)


class NotificationType(Enum):
    """Types of notifications that can be sent to users."""

    # Balance notifications
    BALANCE_TOPUP = 'balance_topup'
    BALANCE_CHANGE = 'balance_change'
    BALANCE_LOW = 'balance_low'

    # Subscription notifications
    SUBSCRIPTION_ACTIVATED = 'subscription_activated'
    SUBSCRIPTION_EXPIRING = 'subscription_expiring'
    SUBSCRIPTION_EXPIRED = 'subscription_expired'
    SUBSCRIPTION_RENEWED = 'subscription_renewed'
    DEVICE_SLOTS_PURCHASED = 'device_slots_purchased'
    TRAFFIC_PURCHASED = 'traffic_purchased'

    # Autopay notifications
    AUTOPAY_SUCCESS = 'autopay_success'
    AUTOPAY_FAILED = 'autopay_failed'
    AUTOPAY_INSUFFICIENT_FUNDS = 'autopay_insufficient_funds'

    # Daily subscription notifications
    DAILY_DEBIT = 'daily_debit'
    DAILY_INSUFFICIENT_FUNDS = 'daily_insufficient_funds'
    TRAFFIC_RESET = 'traffic_reset'

    # Account notifications
    BAN_NOTIFICATION = 'ban_notification'
    UNBAN_NOTIFICATION = 'unban_notification'
    WARNING_NOTIFICATION = 'warning_notification'

    # Referral notifications
    REFERRAL_BONUS = 'referral_bonus'
    REFERRAL_REGISTERED = 'referral_registered'

    # Partner notifications
    PARTNER_APPLICATION_APPROVED = 'partner_application_approved'
    PARTNER_APPLICATION_REJECTED = 'partner_application_rejected'

    # Withdrawal notifications
    WITHDRAWAL_APPROVED = 'withdrawal_approved'
    WITHDRAWAL_REJECTED = 'withdrawal_rejected'

    # Auth emails
    EMAIL_VERIFICATION = 'email_verification'
    PASSWORD_RESET = 'password_reset'

    # Webhook subscription events
    WEBHOOK_SUB_EXPIRED = 'webhook_sub_expired'
    WEBHOOK_SUB_DISABLED = 'webhook_sub_disabled'
    WEBHOOK_SUB_ENABLED = 'webhook_sub_enabled'
    WEBHOOK_SUB_LIMITED = 'webhook_sub_limited'
    WEBHOOK_SUB_TRAFFIC_RESET = 'webhook_sub_traffic_reset'
    WEBHOOK_SUB_DELETED = 'webhook_sub_deleted'
    WEBHOOK_SUB_REVOKED = 'webhook_sub_revoked'
    WEBHOOK_SUB_EXPIRING = 'webhook_sub_expiring'
    WEBHOOK_SUB_FIRST_CONNECTED = 'webhook_sub_first_connected'
    WEBHOOK_SUB_BANDWIDTH_THRESHOLD = 'webhook_sub_bandwidth_threshold'
    WEBHOOK_USER_NOT_CONNECTED = 'webhook_user_not_connected'
    WEBHOOK_DEVICE_ADDED = 'webhook_device_added'
    WEBHOOK_DEVICE_DELETED = 'webhook_device_deleted'

    # Other
    BROADCAST = 'broadcast'
    PAYMENT_RECEIVED = 'payment_received'


class NotificationDeliveryService:
    """
    Service for delivering notifications to users through appropriate channels.

    A user can receive the same event through Telegram, email and the cabinet.
    A failure in one channel never blocks the remaining channels or business flow.
    """

    def __init__(self):
        self._email_service = None
        self._email_templates = None
        self._ws_manager = None

    @property
    def email_service(self):
        """Lazy load email service."""
        if self._email_service is None:
            from app.cabinet.services.email_service import email_service

            self._email_service = email_service
        return self._email_service

    @property
    def email_templates(self):
        """Lazy load email templates."""
        if self._email_templates is None:
            from app.cabinet.services.email_templates import EmailNotificationTemplates

            self._email_templates = EmailNotificationTemplates()
        return self._email_templates

    @property
    def ws_manager(self):
        """Lazy load WebSocket manager."""
        if self._ws_manager is None:
            from app.cabinet.routes.websocket import cabinet_ws_manager

            self._ws_manager = cabinet_ws_manager
        return self._ws_manager

    async def send_notification(
        self,
        user: User,
        notification_type: NotificationType,
        context: dict[str, Any],
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """
        Send a notification through every available channel.

        Args:
            user: User to notify
            notification_type: Type of notification
            context: Context data for message formatting
            bot: Telegram bot instance (required for Telegram users)
            telegram_message: Pre-formatted Telegram message (optional)
            telegram_markup: Telegram keyboard markup (optional)

        Returns:
            True if notification was sent successfully through at least one channel
        """
        try:
            user_status = getattr(user, 'status', None)
            is_ban_event = notification_type is NotificationType.BAN_NOTIFICATION
            if user_status == UserStatus.DELETED.value or (
                user_status == UserStatus.BLOCKED.value and not is_ban_event
            ):
                logger.debug(
                    'Skipping notification for inactive user',
                    user_id=user.id,
                    status=user_status,
                    notification_type_value=notification_type.value,
                )
                return False

            channel_names: list[str] = []
            deliveries: list[Any] = []

            if getattr(user, 'telegram_id', None) and bot and telegram_message:
                channel_names.append('telegram')
                deliveries.append(
                    self._send_telegram_notification(
                        user=user,
                        notification_type=notification_type,
                        context=context,
                        bot=bot,
                        message=telegram_message,
                        markup=telegram_markup,
                    )
                )

            has_verified_email = bool(getattr(user, 'email', None) and getattr(user, 'email_verified', False))
            if has_verified_email and settings.are_user_email_notifications_enabled():
                channel_names.append('email')
                deliveries.append(
                    self._send_email_notification(
                        user,
                        notification_type,
                        context,
                        fallback_message=telegram_message,
                    )
                )

            channel_names.append('websocket')
            deliveries.append(self._send_websocket_notification(user, notification_type, context))

            if not deliveries:
                logger.debug(
                    'No configured notification channel is available for user',
                    user_id=user.id,
                    notification_type_value=notification_type.value,
                )
                return False

            results = await asyncio.gather(*deliveries, return_exceptions=True)
            delivery_results = {channel: result is True for channel, result in zip(channel_names, results, strict=True)}
            delivered = any(delivery_results.values())

            log = logger.info if delivered else logger.warning
            log(
                'User notification delivery completed',
                notification_type_value=notification_type.value,
                user_id=user.id,
                channels=delivery_results,
            )
            return delivered
        except Exception as error:
            logger.error(
                'Unexpected error during notification delivery (suppressed to protect business flow)',
                user_id=getattr(user, 'id', None),
                notification_type_value=getattr(notification_type, 'value', str(notification_type)),
                error=error,
                exc_info=True,
            )
            return False

    async def _send_telegram_notification(
        self,
        user: User,
        notification_type: NotificationType,
        context: dict[str, Any],
        bot: Bot | None,
        message: str | None,
        markup: Any | None,
    ) -> bool:
        """Send notification via Telegram bot."""
        if not bot:
            logger.warning('Bot instance not provided for Telegram notification to user', telegram_id=user.telegram_id)
            return False

        if not message:
            logger.warning(
                'No Telegram message provided for notification to user',
                notification_type_value=notification_type.value,
                telegram_id=user.telegram_id,
            )
            return False

        try:
            from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

            safe_markup = await strip_bot_menu_buttons_for_ultima(markup)
            await asyncio.wait_for(
                bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    reply_markup=safe_markup,
                    parse_mode='HTML',
                ),
                timeout=15.0,
            )
            return True

        except TimeoutError:
            logger.warning('Timeout при отправке Telegram уведомления пользователю', telegram_id=user.telegram_id)
            return False

        except TelegramForbiddenError:
            logger.warning('Telegram user заблокировал бота', telegram_id=user.telegram_id)
            return False

        except TelegramBadRequest as e:
            logger.warning('Ошибка отправки Telegram уведомления пользователю', telegram_id=user.telegram_id, e=e)
            return False

        except Exception as e:
            logger.error('Неожиданная ошибка при отправке Telegram уведомления', e=e)
            return False

    async def _send_email_notification(
        self,
        user: User,
        notification_type: NotificationType,
        context: dict[str, Any],
        fallback_message: str | None = None,
    ) -> bool:
        """Send notification via email."""
        if not self.email_service.is_configured():
            logger.debug('SMTP не настроен, пропускаем email уведомление')
            return False

        if not user.email or not user.email_verified:
            logger.debug('У пользователя нет подтверждённого email', user_id=user.id)
            return False

        try:
            # Get email template (check DB override first, then fall back to hardcoded)
            language = user.language or 'ru'

            # Try DB override
            template = None
            try:
                from app.cabinet.services.email_template_overrides import get_template_override

                override = await get_template_override(notification_type.value, language)
                if override:
                    # Wrap custom body in base template
                    full_html = self.email_templates._get_base_template(override['body_html'], language)
                    template = {
                        'subject': override['subject'],
                        'body_html': full_html,
                    }
            except Exception as e:
                logger.debug('Не удалось проверить override шаблона', e=e)

            if not template:
                template = self.email_templates.get_template(notification_type, language, context)

            if not template and fallback_message:
                template = self.email_templates.get_generic_notification_template(
                    notification_type,
                    language,
                    fallback_message,
                )

            if not template:
                logger.warning('Не найден email шаблон для', notification_type_value=notification_type.value)
                return False

            # Send email (sync smtplib — run in thread to avoid blocking event loop)
            success = await asyncio.to_thread(
                self.email_service.send_email,
                to_email=user.email,
                subject=template['subject'],
                body_html=template['body_html'],
                body_text=template.get('body_text'),
            )

            if success:
                logger.info(
                    'Email уведомление отправлено пользователю',
                    notification_type_value=notification_type.value,
                    user_id=user.id,
                    email=user.email,
                )

            return success

        except Exception as e:
            logger.error('Ошибка отправки email уведомления пользователю', user_id=user.id, e=e)
            return False

    async def send_email_copy(
        self,
        user: User,
        notification_type: NotificationType,
        context: dict[str, Any],
        fallback_message: str | None = None,
    ) -> bool:
        """Send only an email copy without affecting Telegram delivery."""
        if not settings.are_user_email_notifications_enabled():
            return False
        if not getattr(user, 'email', None) or not getattr(user, 'email_verified', False):
            return False
        if getattr(user, 'status', None) == UserStatus.DELETED.value:
            return False

        try:
            return await self._send_email_notification(
                user,
                notification_type,
                context,
                fallback_message=fallback_message,
            )
        except Exception as error:
            logger.error(
                'Email copy delivery failed (suppressed to protect business flow)',
                user_id=getattr(user, 'id', None),
                notification_type_value=notification_type.value,
                error=error,
                exc_info=True,
            )
            return False

    async def _send_websocket_notification(
        self,
        user: User,
        notification_type: NotificationType,
        context: dict[str, Any],
    ) -> bool:
        """Send notification via WebSocket to cabinet."""
        try:
            message = {
                'type': f'notification.{notification_type.value}',
                **context,
            }

            return await self.ws_manager.send_to_user(user.id, message)

        except Exception as e:
            logger.debug('WebSocket уведомление не отправлено пользователю', user_id=user.id, e=e)
            return False

    # ============================================================================
    # Convenience methods for common notification types
    # ============================================================================

    async def notify_balance_topup(
        self,
        user: User,
        amount_kopeks: int,
        new_balance_kopeks: int,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about balance top-up."""
        context = {
            'amount_kopeks': amount_kopeks,
            'amount_rubles': amount_kopeks / 100,
            'new_balance_kopeks': new_balance_kopeks,
            'new_balance_rubles': new_balance_kopeks / 100,
            'formatted_amount': settings.format_price(amount_kopeks),
            'formatted_balance': settings.format_price(new_balance_kopeks),
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.BALANCE_TOPUP,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_subscription_expiring(
        self,
        user: User,
        days_left: int,
        expires_at: Any,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about expiring subscription."""
        context = {
            'days_left': days_left,
            'expires_at': str(expires_at),
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.SUBSCRIPTION_EXPIRING,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_subscription_expired(
        self,
        user: User,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about expired subscription."""
        return await self.send_notification(
            user=user,
            notification_type=NotificationType.SUBSCRIPTION_EXPIRED,
            context={},
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_autopay_success(
        self,
        user: User,
        amount_kopeks: int,
        new_expires_at: Any,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about successful autopay."""
        context = {
            'amount_kopeks': amount_kopeks,
            'amount_rubles': amount_kopeks / 100,
            'formatted_amount': settings.format_price(amount_kopeks),
            'new_expires_at': str(new_expires_at),
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.AUTOPAY_SUCCESS,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_autopay_failed(
        self,
        user: User,
        reason: str,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about failed autopay."""
        context = {
            'reason': reason,
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.AUTOPAY_FAILED,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_ban(
        self,
        user: User,
        reason: str | None = None,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about account ban."""
        context = {
            'reason': reason or 'Нарушение правил использования',
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.BAN_NOTIFICATION,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_unban(
        self,
        user: User,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about account unban."""
        return await self.send_notification(
            user=user,
            notification_type=NotificationType.UNBAN_NOTIFICATION,
            context={},
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_referral_bonus(
        self,
        user: User,
        bonus_kopeks: int,
        referral_name: str,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about referral bonus."""
        context = {
            'bonus_kopeks': bonus_kopeks,
            'bonus_rubles': bonus_kopeks / 100,
            'formatted_bonus': settings.format_price(bonus_kopeks),
            'referral_name': referral_name,
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.REFERRAL_BONUS,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )

    async def notify_partner_approved(
        self,
        user: User,
        commission_percent: int,
        comment: str | None = None,
        bot: Bot | None = None,
        telegram_message: str | None = None,
    ) -> bool:
        """Notify user about partner application approval."""
        context = {
            'commission_percent': commission_percent,
            'comment': comment or '',
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.PARTNER_APPLICATION_APPROVED,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
        )

    async def notify_partner_rejected(
        self,
        user: User,
        comment: str | None = None,
        bot: Bot | None = None,
        telegram_message: str | None = None,
    ) -> bool:
        """Notify user about partner application rejection."""
        context = {
            'comment': comment or '',
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.PARTNER_APPLICATION_REJECTED,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
        )

    async def notify_withdrawal_approved(
        self,
        user: User,
        amount_kopeks: int,
        comment: str | None = None,
        bot: Bot | None = None,
        telegram_message: str | None = None,
    ) -> bool:
        """Notify user about withdrawal request approval."""
        context = {
            'amount_kopeks': amount_kopeks,
            'amount_rubles': amount_kopeks / 100,
            'formatted_amount': settings.format_price(amount_kopeks),
            'comment': comment or '',
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.WITHDRAWAL_APPROVED,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
        )

    async def notify_withdrawal_rejected(
        self,
        user: User,
        amount_kopeks: int,
        comment: str | None = None,
        bot: Bot | None = None,
        telegram_message: str | None = None,
    ) -> bool:
        """Notify user about withdrawal request rejection."""
        context = {
            'amount_kopeks': amount_kopeks,
            'amount_rubles': amount_kopeks / 100,
            'formatted_amount': settings.format_price(amount_kopeks),
            'comment': comment or '',
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.WITHDRAWAL_REJECTED,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
        )

    async def notify_daily_debit(
        self,
        user: User,
        amount_kopeks: int,
        new_balance_kopeks: int,
        bot: Bot | None = None,
        telegram_message: str | None = None,
        telegram_markup: Any | None = None,
    ) -> bool:
        """Notify user about daily subscription debit."""
        context = {
            'amount_kopeks': amount_kopeks,
            'amount_rubles': amount_kopeks / 100,
            'formatted_amount': settings.format_price(amount_kopeks),
            'new_balance_kopeks': new_balance_kopeks,
            'new_balance_rubles': new_balance_kopeks / 100,
            'formatted_balance': settings.format_price(new_balance_kopeks),
        }

        return await self.send_notification(
            user=user,
            notification_type=NotificationType.DAILY_DEBIT,
            context=context,
            bot=bot,
            telegram_message=telegram_message,
            telegram_markup=telegram_markup,
        )


# Singleton instance
notification_delivery_service = NotificationDeliveryService()
