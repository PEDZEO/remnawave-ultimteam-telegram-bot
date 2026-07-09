from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.webserver.security_headers import install_security_headers


def test_security_headers_are_added_for_https_requests() -> None:
    app = FastAPI()
    install_security_headers(app)

    @app.get('/health')
    async def health() -> dict[str, bool]:
        return {'ok': True}

    response = TestClient(app).get('/health', headers={'X-Forwarded-Proto': 'https'})

    assert response.status_code == 200
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'SAMEORIGIN'
    assert response.headers['strict-transport-security'].startswith('max-age=31536000')
