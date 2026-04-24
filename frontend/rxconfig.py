import reflex as rx

from reflex.plugins import SitemapPlugin

config = rx.Config(
    app_name="frontend",
    # Tell the frontend to talk to the Reflex internal backend on port 8000
    api_url="http://127.0.0.1:8000",
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    # Disable the sitemap plugin to remove the warning message
    disable_plugins=[
        SitemapPlugin,
    ],
    state_auto_setters=True,
)