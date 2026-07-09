"""OAuth 2.0 provider implementations for cabinet authentication."""

import asyncio
import base64
import hashlib
import json
import secrets
from abc import ABC, abstractmethod
from typing import TypedDict

import httpx
import structlog
from pydantic import BaseModel

from app.config import settings
from app.utils.cache import cache, cache_key


logger = structlog.get_logger(__name__)

STATE_TTL_SECONDS = 600  # 10 minutes


# --- Typed dicts for provider API responses ---


class OAuthProviderConfig(TypedDict):
    client_id: str
    client_secret: str
    enabled: bool
    display_name: str


class OAuthTokenResponse(TypedDict, total=False):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
    # VK-specific: email and user_id can be included
    email: str
    user_id: int
    state: str
    id_token: str


class GoogleUserInfoResponse(TypedDict, total=False):
    sub: str
    email: str
    email_verified: bool
    given_name: str
    family_name: str
    picture: str
    name: str


class YandexUserInfoResponse(TypedDict, total=False):
    id: str
    login: str
    default_email: str
    emails: list[str]
    first_name: str
    last_name: str
    default_avatar_id: str


class DiscordUserInfoResponse(TypedDict, total=False):
    id: str
    username: str
    global_name: str
    email: str
    verified: bool
    avatar: str


class VKIDUserData(TypedDict, total=False):
    user_id: str | int
    email: str
    nickname: str
    screen_name: str
    domain: str
    first_name: str
    last_name: str
    avatar: str
    firstName: str
    lastName: str
    avatar_url: str


class VKIDUserInfoResponse(TypedDict, total=False):
    user: VKIDUserData


class OAuthStatePayload(TypedDict, total=False):
    provider: str
    code_verifier: str
    intent: str
    target_user_id: int


# --- Models ---


class OAuthUserInfo(BaseModel):
    """Normalized user info from OAuth provider."""

    provider: str
    provider_id: str
    email: str | None = None
    email_verified: bool = False
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None


# --- CSRF state management (Redis) ---


def _build_pkce_pair() -> tuple[str, str]:
    """Build PKCE code verifier/challenge pair (S256)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')
    return verifier, challenge


async def generate_oauth_state(provider: str, payload: OAuthStatePayload | None = None) -> str:
    """Generate a CSRF state token for OAuth flow. Stored in Redis with TTL."""
    state = secrets.token_urlsafe(32)
    state_payload: OAuthStatePayload = {'provider': provider}
    if payload:
        state_payload.update(payload)
    await cache.set(cache_key('oauth_state', state), json.dumps(state_payload), expire=STATE_TTL_SECONDS)
    return state


def _decode_oauth_state(stored_value: str) -> OAuthStatePayload:
    try:
        return json.loads(stored_value)
    except json.JSONDecodeError:
        return {'provider': stored_value}


async def peek_oauth_state_any(state: str) -> OAuthStatePayload | None:
    """Read state context without consuming the one-time token."""
    key = cache_key('oauth_state', state)
    stored_value: str | None = await cache.get(key)
    if stored_value is None:
        return None
    return _decode_oauth_state(stored_value)


async def consume_oauth_state_any(state: str) -> OAuthStatePayload | None:
    """Consume a CSRF state token and return raw payload without provider pre-validation."""
    key = cache_key('oauth_state', state)
    stored_value: str | None = await cache.get(key)
    if stored_value is None:
        return None
    await cache.delete(key)
    return _decode_oauth_state(stored_value)


async def consume_oauth_state(state: str, provider: str) -> OAuthStatePayload | None:
    """Validate and consume a CSRF state token from Redis."""
    payload = await consume_oauth_state_any(state)
    if payload is None:
        return None
    if payload.get('provider') != provider:
        return None
    return payload


async def validate_oauth_state(state: str, provider: str) -> bool:
    """Validate and consume a CSRF state token from Redis."""
    payload = await consume_oauth_state(state, provider)
    return payload is not None


# --- Provider implementations ---


class OAuthProvider(ABC):
    """Base class for OAuth 2.0 providers."""

    name: str
    display_name: str

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @abstractmethod
    def get_authorization_url(self, state: str, **kwargs: str) -> str:
        """Build the authorization URL for the provider."""

    @abstractmethod
    async def exchange_code(self, code: str, **kwargs: str) -> OAuthTokenResponse:
        """Exchange authorization code for tokens."""

    @abstractmethod
    async def get_user_info(self, token_data: OAuthTokenResponse) -> OAuthUserInfo:
        """Fetch user info from the provider."""


class GoogleProvider(OAuthProvider):
    name = 'google'
    display_name = 'Google'

    AUTHORIZE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

    def get_authorization_url(self, state: str, **kwargs: str) -> str:
        params: dict[str, str] = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'select_account',
        }
        request = httpx.Request('GET', self.AUTHORIZE_URL, params=params)
        return str(request.url)

    async def exchange_code(self, code: str, **kwargs: str) -> OAuthTokenResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.TOKEN_URL,
                json={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.redirect_uri,
                },
            )
            response.raise_for_status()
            data: OAuthTokenResponse = response.json()
            return data

    async def get_user_info(self, token_data: OAuthTokenResponse) -> OAuthUserInfo:
        access_token = token_data['access_token']
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            data: GoogleUserInfoResponse = response.json()

        return OAuthUserInfo(
            provider='google',
            provider_id=str(data['sub']),
            email=data.get('email'),
            email_verified=data.get('email_verified', False),
            first_name=data.get('given_name'),
            last_name=data.get('family_name'),
            avatar_url=data.get('picture'),
        )


class YandexProvider(OAuthProvider):
    name = 'yandex'
    display_name = 'Yandex'

    AUTHORIZE_URL = 'https://oauth.yandex.ru/authorize'
    TOKEN_URL = 'https://oauth.yandex.com/token'
    USERINFO_URL = 'https://login.yandex.ru/info'
    TOKEN_URLS = ('https://oauth.yandex.com/token', 'https://oauth.yandex.ru/token')
    USERINFO_URLS = ('https://login.yandex.ru/info', 'https://login.yandex.com/info')

    @staticmethod
    def _is_retryable_http_error(exc: Exception) -> bool:
        if isinstance(
            exc,
            (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.RemoteProtocolError,
            ),
        ):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code >= 500
        return False

    def get_authorization_url(self, state: str, **kwargs: str) -> str:
        params: dict[str, str] = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'login:info login:email',
            'state': state,
            'force_confirm': 'yes',
        }
        request = httpx.Request('GET', self.AUTHORIZE_URL, params=params)
        return str(request.url)

    async def exchange_code(self, code: str, **kwargs: str) -> OAuthTokenResponse:
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
        }
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=30) as client:
            for token_url in self.TOKEN_URLS:
                for attempt in range(3):
                    try:
                        response = await client.post(token_url, data=data)
                        response.raise_for_status()
                        return response.json()
                    except Exception as exc:
                        last_error = exc
                        if not self._is_retryable_http_error(exc):
                            raise
                        if attempt < 2:
                            await asyncio.sleep(0.4 * (attempt + 1))
                            continue
                        logger.warning(
                            'Yandex token exchange retry exhausted for endpoint',
                            endpoint=token_url,
                            attempt=attempt + 1,
                            exc=exc,
                        )
        if last_error:
            raise last_error
        raise RuntimeError('Yandex token exchange failed without explicit error')

    async def get_user_info(self, token_data: OAuthTokenResponse) -> OAuthUserInfo:
        access_token = token_data['access_token']
        last_error: Exception | None = None
        headers = {'Authorization': f'OAuth {access_token}'}
        params = {'format': 'json'}

        async with httpx.AsyncClient(timeout=30) as client:
            for userinfo_url in self.USERINFO_URLS:
                for attempt in range(3):
                    try:
                        response = await client.get(userinfo_url, params=params, headers=headers)
                        response.raise_for_status()
                        data: YandexUserInfoResponse = response.json()
                        break
                    except Exception as exc:
                        last_error = exc
                        if not self._is_retryable_http_error(exc):
                            raise
                        if attempt < 2:
                            await asyncio.sleep(0.4 * (attempt + 1))
                            continue
                        logger.warning(
                            'Yandex user info retry exhausted for endpoint',
                            endpoint=userinfo_url,
                            attempt=attempt + 1,
                            exc=exc,
                        )
                else:
                    continue
                break
            else:
                if last_error:
                    raise last_error
                raise RuntimeError('Yandex user info fetch failed without explicit error')

        default_email = data.get('default_email')
        emails = data.get('emails', [])
        email = default_email or (emails[0] if emails else None)

        return OAuthUserInfo(
            provider='yandex',
            provider_id=str(data['id']),
            email=email,
            email_verified=bool(email),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            username=data.get('login'),
            avatar_url=(
                f'https://avatars.yandex.net/get-yapic/{data["default_avatar_id"]}/islands-200'
                if data.get('default_avatar_id')
                else None
            ),
        )


class DiscordProvider(OAuthProvider):
    name = 'discord'
    display_name = 'Discord'

    AUTHORIZE_URL = 'https://discord.com/api/oauth2/authorize'
    TOKEN_URL = 'https://discord.com/api/oauth2/token'
    USERINFO_URL = 'https://discord.com/api/v10/users/@me'

    def get_authorization_url(self, state: str, **kwargs: str) -> str:
        params: dict[str, str] = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'identify email',
            'state': state,
            'prompt': 'consent',
        }
        request = httpx.Request('GET', self.AUTHORIZE_URL, params=params)
        return str(request.url)

    async def exchange_code(self, code: str, **kwargs: str) -> OAuthTokenResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.redirect_uri,
                },
            )
            response.raise_for_status()
            data: OAuthTokenResponse = response.json()
            return data

    async def get_user_info(self, token_data: OAuthTokenResponse) -> OAuthUserInfo:
        access_token = token_data['access_token']
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            data: DiscordUserInfoResponse = response.json()

        avatar_url: str | None = None
        if data.get('avatar'):
            avatar_url = f'https://cdn.discordapp.com/avatars/{data["id"]}/{data["avatar"]}.png'

        return OAuthUserInfo(
            provider='discord',
            provider_id=str(data['id']),
            email=data.get('email'),
            email_verified=data.get('verified', False),
            first_name=data.get('global_name') or data.get('username'),
            username=data.get('username'),
            avatar_url=avatar_url,
        )


class VKProvider(OAuthProvider):
    name = 'vk'
    display_name = 'VK'

    AUTHORIZE_URL = 'https://id.vk.ru/authorize'
    TOKEN_URL = 'https://id.vk.ru/oauth2/auth'
    USERINFO_URL = 'https://id.vk.ru/oauth2/user_info'
    CODE_CHALLENGE_METHOD = 'S256'

    @staticmethod
    def _decode_id_token_payload(id_token: str | None) -> dict[str, str]:
        """Decode JWT payload without verification for non-critical profile fallbacks."""
        if not id_token:
            return {}
        try:
            parts = id_token.split('.')
            if len(parts) < 2:
                return {}
            payload_b64 = parts[1]
            payload_b64 += '=' * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
            payload = json.loads(payload_json)
            if isinstance(payload, dict):
                return payload
        except Exception:
            return {}
        return {}

    def get_authorization_url(self, state: str, **kwargs: str) -> str:
        code_challenge = kwargs.get('code_challenge')
        if not code_challenge:
            raise ValueError('Missing VK PKCE code challenge')
        params: dict[str, str] = {
            'app_id': self.client_id,
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'email',
            'code_challenge': code_challenge,
            'code_challenge_method': self.CODE_CHALLENGE_METHOD,
            'state': state,
        }
        request = httpx.Request('GET', self.AUTHORIZE_URL, params=params)
        return str(request.url)

    async def exchange_code(self, code: str, **kwargs: str) -> OAuthTokenResponse:
        device_id = kwargs.get('device_id')
        code_verifier = kwargs.get('code_verifier')
        request_state = kwargs.get('state')
        if not device_id or not code_verifier:
            raise ValueError('Missing VK device_id or code_verifier')

        query_params = {
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'code_verifier': code_verifier,
            'device_id': device_id,
            'state': request_state or '',
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.TOKEN_URL,
                params=query_params,
                data={'code': code},
            )
            response.raise_for_status()
            data: OAuthTokenResponse = response.json()
            return data

    async def get_user_info(self, token_data: OAuthTokenResponse) -> OAuthUserInfo:
        access_token = token_data['access_token']
        email: str | None = token_data.get('email')
        id_token_claims = self._decode_id_token_payload(token_data.get('id_token'))

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.USERINFO_URL,
                data={'access_token': access_token},
            )
            response.raise_for_status()
            data: VKIDUserInfoResponse = response.json()

        user_data: VKIDUserData = data.get('user', {}) or {}
        provider_id = str(
            user_data.get('user_id') or token_data.get('user_id') or id_token_claims.get('sub') or '',
        )
        resolved_email = email or user_data.get('email') or id_token_claims.get('email')
        first_name = (
            user_data.get('first_name')
            or user_data.get('firstName')
            or id_token_claims.get('given_name')
            or id_token_claims.get('first_name')
        )
        last_name = (
            user_data.get('last_name')
            or user_data.get('lastName')
            or id_token_claims.get('family_name')
            or id_token_claims.get('last_name')
        )
        username = (
            user_data.get('screen_name')
            or user_data.get('nickname')
            or user_data.get('domain')
            or id_token_claims.get('preferred_username')
        )
        if not username and resolved_email:
            username = resolved_email.split('@')[0]
        if not username and provider_id:
            username = f'vk_{provider_id}'
        if not first_name and username:
            first_name = username
        avatar_url = user_data.get('avatar') or user_data.get('avatar_url') or id_token_claims.get('picture')

        return OAuthUserInfo(
            provider='vk',
            provider_id=provider_id,
            email=resolved_email,
            email_verified=bool(resolved_email),
            first_name=first_name,
            last_name=last_name,
            username=username,
            avatar_url=avatar_url,
        )


# --- Provider factory ---

_PROVIDERS: dict[str, type[OAuthProvider]] = {
    'google': GoogleProvider,
    'yandex': YandexProvider,
    'discord': DiscordProvider,
    'vk': VKProvider,
}


def get_provider(name: str) -> OAuthProvider | None:
    """Get an OAuth provider instance if enabled.

    Returns None if the provider is not enabled or not found.
    """
    providers_config: dict[str, OAuthProviderConfig] = settings.get_oauth_providers_config()
    config = providers_config.get(name)
    if not config or not config['enabled']:
        return None

    provider_class = _PROVIDERS.get(name)
    if not provider_class:
        return None

    redirect_uri = f'{settings.CABINET_URL}/auth/oauth/callback'

    return provider_class(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        redirect_uri=redirect_uri,
    )


def build_vk_pkce_payload() -> tuple[OAuthStatePayload, str]:
    """Generate extra OAuth state payload for VK ID PKCE flow."""
    code_verifier, code_challenge = _build_pkce_pair()
    return {
        'code_verifier': code_verifier,
        'provider': 'vk',
    }, code_challenge
