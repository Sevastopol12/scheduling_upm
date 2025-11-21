import reflex as rx

config = rx.Config(
    app_name="scheduling_problem",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)