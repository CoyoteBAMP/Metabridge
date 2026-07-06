import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY
from app.routers import auth as auth_router
from app.routers import meta_webhook
from app.routers.web import dashboard, inbox, accounts, webhooks, monitor
from app.routers.web import templates as templates_web, settings, setup
from app.routers.api import messages as api_messages, conversations as api_conversations
from app.routers.api import accounts as api_accounts, webhooks as api_webhooks

app = FastAPI(title="Metabridge", docs_url="/docs", redoc_url=None)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=False)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers web
app.include_router(auth_router.router)
app.include_router(meta_webhook.router)
app.include_router(dashboard.router)
app.include_router(inbox.router)
app.include_router(accounts.router)
app.include_router(webhooks.router)
app.include_router(monitor.router)
app.include_router(templates_web.router)
app.include_router(settings.router)
app.include_router(setup.router)

# Routers API pública
app.include_router(api_messages.router, prefix="/api/v1")
app.include_router(api_conversations.router, prefix="/api/v1")
app.include_router(api_accounts.router, prefix="/api/v1")
app.include_router(api_webhooks.router, prefix="/api/v1")


@app.get("/")
def root():
    return RedirectResponse("/login")
