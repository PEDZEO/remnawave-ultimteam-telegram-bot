"""Baseline browser security headers shared by cabinet and API applications."""

from fastapi import FastAPI, Request


def install_security_headers(app: FastAPI) -> None:
    if getattr(app.state, 'security_headers_installed', False):
        return
    app.state.security_headers_installed = True

    @app.middleware('http')
    async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')

        forwarded_proto = request.headers.get('x-forwarded-proto', '').split(',', 1)[0].strip().lower()
        if request.url.scheme == 'https' or forwarded_proto == 'https':
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return response
