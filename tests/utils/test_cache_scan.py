from unittest.mock import AsyncMock

import pytest

from app.utils.cache import CacheService


class FakeRedis:
    def __init__(self, keys: list[bytes]):
        self.keys = keys
        self.unlink = AsyncMock(side_effect=lambda *items: len(items))
        self.keys_command = AsyncMock(side_effect=AssertionError('KEYS must not be used'))

    async def scan_iter(self, *, match: str, count: int):
        assert match == 'available_countries*'
        assert count == 500
        for key in self.keys:
            yield key


@pytest.mark.asyncio
async def test_delete_pattern_scans_and_unlinks_in_bounded_batches() -> None:
    service = CacheService()
    fake_redis = FakeRedis([f'available_countries:{index}'.encode() for index in range(1001)])
    service.redis_client = fake_redis  # type: ignore[assignment]
    service._connected = True

    deleted = await service.delete_pattern('available_countries*')

    assert deleted == 1001
    assert [call.args for call in fake_redis.unlink.await_args_list] == [
        tuple(fake_redis.keys[:500]),
        tuple(fake_redis.keys[500:1000]),
        tuple(fake_redis.keys[1000:]),
    ]


@pytest.mark.asyncio
async def test_get_keys_uses_scan() -> None:
    service = CacheService()
    fake_redis = FakeRedis([b'available_countries:ru', b'available_countries:nl'])
    service.redis_client = fake_redis  # type: ignore[assignment]
    service._connected = True

    keys = await service.get_keys('available_countries*')

    assert keys == ['available_countries:ru', 'available_countries:nl']
