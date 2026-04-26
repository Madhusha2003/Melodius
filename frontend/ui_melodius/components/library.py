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
        rx.cond(
            State.tracks,
            rx.box(
                rx.foreach(
                    State.filtered_tracks,
                    lambda track: rx.hstack(
                        rx.box(
                            rx.cond(
                                track.cover_url,
                                rx.image(
                                    src=track.cover_url,
                                    key=track.url, # Force re-render
                                    width="42px",
                                    height="42px",
                                    border_radius="8px",
                                    object_fit="cover",
                                ),
                                rx.center(
                                    rx.icon(tag="music", size=20, color="gray"),
                                    width="42px",
                                    height="42px",
                                    background="var(--gray-4)",
                                    border_radius="8px",
                                )
                            ),
                            transition="all 0.2s ease",
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
                        _hover={
                            "background": "var(--gray-3)",
                            "transform": "translateX(4px)",
                        },
                        transition="all 0.2s ease",
                        align_items="center",
                        spacing="4",
                        cursor="pointer",
                        on_click=lambda: State.play_track(track),
                    )
                ),
                width="100%",
                display="flex",
                flex_direction="column",
                gap="0.5em",
                flex="1",
                overflow_y="auto",
                padding_right="0.5em",
            ),
            rx.center(
                rx.vstack(
                    rx.icon(tag="music_2", size=48, color="gray", opacity=0.5),
                    rx.text("Your library is empty", size="4", font_weight="bold"),
                    rx.text("Click 'Scan Music' to find your tracks", size="2", color="gray"),
                    rx.button(
                        "Scan Now",
                        on_click=State.scan_music,
                        margin_top="1em",
                        variant="soft",
                        cursor="pointer",
                    ),
                    spacing="2",
                    align_items="center",
                ),
                padding="4em",
                width="100%",
            )
        ),
        width="100%",
        padding="1.5em",
        background=rx.color_mode_cond(
            light="rgba(255, 255, 255, 0.9)", 
            dark="rgba(15, 15, 15, 0.9)"
        ),
        border="1px solid",
        border_color=rx.color_mode_cond(
            light="rgba(0,0,0,0.05)",
            dark="rgba(255,255,255,0.05)"
        ),
        border_radius="24px",
        box_shadow="0 10px 40px rgba(0,0,0,0.05)",
        flex="1",
        height="100%",
    )
