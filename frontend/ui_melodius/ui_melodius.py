import reflex as rx
from .state.base import State
from .components.header import header
from .components.library import library_view
from .components.player import player_bar
from .components.equalizer.equalizer import equalizer_ui

def index() -> rx.Component:
    return rx.box(
        # 1. THE ENGINE (Hidden Audio Player)
        rx.audio(
            id="audio-player",
            src=State.current_track.url,
            playing=State.is_playing,
            volume=State.volume,
            on_ended=State.next_track,
            controls=False,
            custom_attrs={"crossOrigin": "anonymous"}
        ),

        # 2. Header
        header(),

        # 3. Main Layout (Library + Equalizer)
        rx.center(
            rx.hstack(
                # Left side: Library
                library_view(),
                
                # Right Side: Equalizer
                rx.cond(
                    State.current_track.url != "",
                    rx.vstack(
                        equalizer_ui(),
                        width="100%",
                        flex="0.5",
                        height="100%",
                        padding="2.5em",
                        background="var(--gray-2)",
                        border_radius="24px",
                        justify_content="center",
                    )
                ),
                
                width="100%",
                max_width="95%",
                align_items="stretch",
                spacing="6",
                padding_bottom="160px",
            ),
            width="100%",
            flex="1",
        ),

        # 4. Bottom Player Bar
        player_bar(),

        background="black",
        color="white",
        height="100vh",
        display="flex",
        flex_direction="column",
        overflow="hidden",
        on_mount=[State.fetch_tracks, State.hide_ghost_box],
    )

global_styles = {
    "a[href*='reflex.dev']": {
        "display": "none !important",
    }
}

app = rx.App(style=global_styles)
app.add_page(index, on_load=[State.on_load])