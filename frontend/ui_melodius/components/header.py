import reflex as rx

def header():
    return rx.hstack(
        rx.icon(tag="audio-waveform", size=32, color="var(--accent-9)"),
        rx.heading("Melodius", size="7", font_weight="bold", letter_spacing="-0.02em"),
        width="100%",
        padding="2em",
        align_items="center",
        spacing="3",
    )
