import reflex as rx
from ..state.base import State
from .search_bar.search_bar import search_bar_ui

def library_view():
    return rx.vstack(
        rx.hstack(
            rx.heading("Your Library", size="5", font_weight="600"),
            rx.spacer(),
            search_bar_ui(State.search_query, State.set_search_query),
            rx.button(
                rx.icon(tag="folder_sync"),
                "Scan Music",
                on_click=State.scan_music,
                size="2",
                variant="soft",
                color_scheme="blue",
                border_radius="full",
                cursor="pointer",
            ),
            width="100%",
            padding_bottom="1.5em",
            align_items="center",
            border_bottom="1px solid var(--gray-4)",
            margin_bottom="1em",
        ),
        rx.box(
            rx.foreach(
                State.filtered_tracks,
                lambda track: rx.hstack(
                    rx.box(
                        rx.icon(tag="play", size=18),
                        padding="0.8em",
                        border_radius="full",
                        background="var(--accent-3)",
                        color="var(--accent-11)",
                        cursor="pointer",
                        _hover={"background": "var(--accent-4)", "transform": "scale(1.05)"},
                        transition="all 0.2s ease",
                        on_click=lambda: State.play_track(track),
                    ),
                    rx.vstack(
                        rx.text(track.title, font_weight="600", size="3"),
                        rx.text(track.artist, size="2", color="gray"),
                        align_items="start",
                        spacing="1",
                    ),
                    width="100%",
                    padding="1em",
                    border_radius="12px",
                    _hover={"background": "var(--gray-3)"},
                    transition="background 0.2s ease",
                    align_items="center",
                    spacing="4",
                )
            ),
            width="100%",
            display="flex",
            flex_direction="column",
            gap="0.5em",
            max_height="60vh",
            overflow_y="auto",
            padding_right="0.5em",
        ),
        width="100%",
        padding="2.5em",
        background="var(--gray-2)",
        border_radius="24px",
        box_shadow="0 10px 40px rgba(0,0,0,0.1)",
        flex="1",
        height="100%",
    )
