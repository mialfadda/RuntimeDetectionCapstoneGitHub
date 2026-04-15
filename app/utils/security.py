"""Security headers + HTTPS enforcement (Step 35)."""
from flask import Flask, request, redirect


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def _apply(resp):
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'",
        )
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        if not app.debug:
            resp.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return resp

    @app.before_request
    def _force_https():
        if app.debug or app.testing:
            return None
        if request.is_secure or request.headers.get("X-Forwarded-Proto") == "https":
            return None
        return redirect(request.url.replace("http://", "https://", 1), code=301)
