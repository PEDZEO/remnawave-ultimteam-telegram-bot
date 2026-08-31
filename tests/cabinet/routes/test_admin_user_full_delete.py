from types import SimpleNamespace

import pytest

from app.cabinet.routes import admin_users
from app.cabinet.schemas.users import FullDeleteUserRequest


class _ExpiringUser:
    def __init__(self) -> None:
        self.expired = False

    @property
    def remnawave_uuid(self) -> str:
        if self.expired:
            raise RuntimeError('deleted ORM instance was accessed')
        return 'remnawave-user-uuid'


@pytest.mark.asyncio
async def test_full_delete_does_not_access_user_after_service_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _ExpiringUser()

    async def get_user(_db: object, _user_id: int) -> _ExpiringUser:
        return user

    class UserServiceStub:
        async def delete_user_account(self, _db: object, _user_id: int, _admin_id: int) -> bool:
            user.expired = True
            return True

    monkeypatch.setattr(admin_users, 'get_user_by_id', get_user)
    monkeypatch.setattr('app.services.user_service.UserService', UserServiceStub)

    response = await admin_users.full_delete_user(
        user_id=1983,
        request=FullDeleteUserRequest(delete_from_panel=True),
        admin=SimpleNamespace(id=142),
        db=object(),
    )

    assert response.success is True
    assert response.deleted_from_bot is True
    assert response.deleted_from_panel is True
