from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from reliable_webhook_api.infrastructure.security import HmacSha256Signer

_SIGNING_PATH = "/docs/webhook-signature"


def configure_development_swagger(
    app: FastAPI,
    *,
    webhook_secret: str,
    signature_header: str,
) -> None:
    """Configure Swagger UI to sign webhook requests in development only."""

    signer = HmacSha256Signer(webhook_secret)

    @app.post(_SIGNING_PATH, include_in_schema=False)
    async def sign_swagger_webhook(request: Request) -> JSONResponse:
        signature = signer.sign(await request.body())
        return JSONResponse({"signature": signature})

    @app.get("/docs", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
        )
        html = response.body.decode()
        script = _build_request_signing_script(signature_header)
        return HTMLResponse(html.replace("</body>", f"{script}</body>"))


def _build_request_signing_script(signature_header: str) -> str:
    return f"""
<script>
const originalRequestInterceptor = ui.getConfigs().requestInterceptor;

ui.getConfigs().requestInterceptor = async (request) => {{
    const url = new URL(request.url, window.location.origin);
    const isWebhookRequest =
        request.method.toUpperCase() === "POST" &&
        url.pathname === "/webhooks/events";

    if (isWebhookRequest) {{
        const response = await fetch("{_SIGNING_PATH}", {{
            method: "POST",
            headers: {{"Content-Type": "text/plain"}},
            body: request.body ?? "",
        }});

        if (!response.ok) {{
            throw new Error("Unable to sign webhook request.");
        }}

        const payload = await response.json();
        request.headers["{signature_header}"] = payload.signature;
    }}

    return originalRequestInterceptor
        ? originalRequestInterceptor(request)
        : request;
}};
</script>
"""
