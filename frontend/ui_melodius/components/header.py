import reflex as rx
from ..state.base import State

def header():
    return rx.hstack(
        rx.hstack(
            rx.icon(tag="audio-waveform", size=32, color="var(--accent-9)"),
            rx.heading("Melodius", size="7", font_weight="bold", letter_spacing="-0.02em"),
            spacing="3",
            align_items="center",
        ),
        rx.spacer(),
        rx.button(
            rx.icon(tag="settings", size=20),
            on_click=State.toggle_settings,
            variant="ghost",
            color_scheme="gray",
            cursor="pointer",
            _hover={"background": "var(--gray-3)"},
        ),
        width="100%",
        padding="2em",
        align_items="center",
    )
