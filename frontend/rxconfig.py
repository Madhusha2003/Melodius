import reflex as rx

config = rx.Config(
    app_name="frontend",
    # Tell the frontend to talk to the Reflex internal backend on port 8000
    api_url="http://localhost:8000",
    cors_allowed_origins=[
        "http://localhost:3000",
    ],
    # Disable the sitemap plugin to remove the warning message
    disable_plugins=[
        "reflex.plugins.sitemap.SitemapPlugin",
    ],
)