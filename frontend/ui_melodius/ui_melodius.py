import reflex as rx
from .state.base import State
from .components.header import header
from .components.library import library_view
from .components.player import player_bar
from .components.settings import settings_view
from .components.equalizer.equalizer import equalizer_ui

def splash_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.box(
                rx.image(src="melodius_icon_1024.png", width="160px", height="160px", border_radius="24px"),
                class_name="splash-logo",
            ),
            rx.heading("Melodius", size="9", font_weight="bold", letter_spacing="-0.04em", margin_top="0.5em"),
            rx.text("Your Symphony, Redefined", size="4", color="gray", opacity=0.7),
            rx.spacer(),
            rx.spinner(size="3", color="var(--accent-9)", margin_top="2em"),
            align_items="center",
            spacing="2",
        ),
        width="100vw",
        height="100vh",
        background="radial-gradient(circle at center, #111111 0%, #000000 100%)",
        position="fixed",
        top="0",
        left="0",
        z_index="1000",
    )


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

        # 2. Main Content
        rx.box(
            # Header
            header(),

            # Main Layout
            rx.box(
                rx.center(
                    rx.hstack(
                        # Left side: Library
                        library_view(),
                        
                        # Right Side: Equalizer
                        rx.cond(
                            State.current_track.url != "",
                            rx.box(
                                equalizer_ui(),
                                width="100%",
                                flex="0.5",
                            )
                        ),
                        
                        width="100%",
                        max_width="95%",
                        height="100%",
                        align_items="stretch",
                        spacing="6",
                    ),
                    width="100%",
                    height="100%",
                ),
                flex="1",
                overflow="hidden",
                padding_top="1em",
                padding_bottom="1em", 
            ),

            # Player Bar
            player_bar(),

            # Settings Sidebar
            settings_view(),

            height="100vh",
            display="flex",
            flex_direction="column",
            overflow="hidden",
            on_mount=[State.fetch_tracks, State.hide_ghost_box],
            background=rx.color_mode_cond(
                light="linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%)",
                dark="linear-gradient(180deg, #0A0A0A 0%, #000000 100%)"
            ),
            class_name="main-content-fade",
            opacity=rx.cond(State.is_loading, "0", "1"),
            transition="opacity 0.5s ease-in-out",
        ),

        # 3. Splash Screen Overlay
        rx.cond(
            State.is_loading,
            splash_screen(),
        )
    )

global_styles = {
    "a[href*='reflex.dev']": {
        "display": "none !important",
    },
    "::-webkit-scrollbar": {
        "display": "none",
    },
    "html, body": {
        "margin": "0",
        "padding": "0",
        "overflow": "hidden",
        "ms-overflow-style": "none",
        "scrollbar-width": "none",
    },
    "@keyframes marquee": {
        "0%": {"transform": "translateX(0)"},
        "100%": {"transform": "translateX(-50%)"},
    },
    ".marquee-text": {
        "display": "inline-block",
        "white-space": "nowrap",
        "padding_right": "50px",
        "animation": "marquee 15s linear infinite",
    },
    ".marquee-container": {
        "overflow": "hidden",
        "white-space": "nowrap",
        "width": "100%",
        "mask-image": "linear-gradient(to right, transparent, black 10%, black 90%, transparent)",
    },
    "@keyframes splash-pulse": {
        "0%": {"transform": "scale(1)", "opacity": "1"},
        "50%": {"transform": "scale(1.1)", "opacity": "0.8"},
        "100%": {"transform": "scale(1)", "opacity": "1"},
    },
    ".splash-logo": {
        "animation": "splash-pulse 2s infinite ease-in-out",
    },
    "@keyframes fade-in": {
        "0%": {"opacity": "0", "transform": "translateY(10px)"},
        "100%": {"opacity": "1", "transform": "translateY(0)"},
    },
    ".main-content-fade": {
        "animation": "fade-in 0.8s ease-out forwards",
    }
}

app = rx.App(
    style=global_styles,
    theme=rx.theme(
        appearance="dark",
        has_background=True,
        accent_color="blue",
        gray_color="slate",
    )
)
app.add_page(index, on_load=[State.on_load])