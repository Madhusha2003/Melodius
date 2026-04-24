import os
import reflex as rx

from reflex.plugins import SitemapPlugin

# Get the ports from environment variables (set by launcher)
port = os.getenv("REFLEX_PORT", "8000")
ui_port = os.getenv("MELODIUS_UI_PORT", "3000")

config = rx.Config(
    app_name="ui_melodius",
    # Tell the frontend to talk to the Reflex internal backend on the dynamic port
    api_url=f"http://127.0.0.1:{port}",
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        f"http://localhost:{port}",
        f"http://127.0.0.1:{port}",
        f"http://localhost:{ui_port}",
        f"http://127.0.0.1:{ui_port}",
        "http://localhost",
        "http://127.0.0.1",
    ],
    # Disable the sitemap plugin to remove the warning message
    disable_plugins=[
        SitemapPlugin,
    ],
)