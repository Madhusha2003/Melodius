import reflex as rx

def search_bar_ui(query_var, on_change) -> rx.Component:
    return rx.box(
        rx.icon(
            "search",
            size=18,
            color="var(--gray-9)",
            position="absolute",
            left="10px",
            top="50%",
            transform="translateY(-50%)",
        ),
        rx.input(
            placeholder="Search artists, songs...",
            value=query_var,
            on_change=on_change,
            size="2",
            radius="full",
            variant="surface",
            width="100%",
            style={
                "padding-left": "2.5em",  # 👈 space for icon
                "background": "var(--gray-3)",
                "transition": "all 0.2s ease",
            },
        ),
        position="relative",   # 👈 needed for absolute icon
        width="100%",
        max_width="350px",
        margin_right="1em",
    )