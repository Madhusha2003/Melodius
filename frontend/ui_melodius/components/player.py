import reflex as rx
from ..state.base import State

def player_controls():
    return rx.vstack(
        rx.hstack(
            rx.button(rx.icon(tag="shuffle"), variant="ghost", color_scheme=rx.cond(State.is_shuffled, "accent", "gray"), on_click=State.toggle_shuffle),
            rx.button(rx.icon(tag="skip_back"), variant="ghost", on_click=State.prev_track),
            rx.button(
                rx.cond(
                    State.is_playing,
                    rx.icon(tag="pause"),
                    rx.icon(tag="play"),
                ),
                size="3", variant="solid", radius="full", 
                on_click=State.toggle_play,
                box_shadow=rx.cond(State.is_playing, "0 0 15px rgba(66, 153, 225, 0.6)", "none"),
            ),
            rx.button(rx.icon(tag="skip_forward"), variant="ghost", on_click=State.next_track),
            spacing="4",
            align_items="center",
        ),
        rx.hstack(
            rx.text(State.formatted_current_time, size="1", color="gray", width="40px", text_align="right"),
            rx.slider(
                value=[State.current_time], 
                min=0, 
                max=State.duration,
                on_change=State.start_dragging, 
                on_value_commit=State.seek,           
                width="100%",                         
                cursor="pointer",
                style={
                    "& .rt-SliderTrack": {
                        "height": "4px !important",
                        "background-color": "rgba(255, 255, 255, 0.2) !important",
                        "cursor": "pointer !important",
                    },
                    "& .rt-SliderRange": {
                        "height": "4px !important",
                        "background-color": "white !important",
                        "transition": "background-color 0.1s ease",
                    },
                    "& .rt-SliderThumb": {
                        "opacity": "0 !important", 
                        "width": "12px !important",
                        "height": "12px !important",
                        "background-color": "white !important",
                        "box-shadow": "0 2px 4px rgba(0,0,0,0.5) !important",
                        "transition": "opacity 0.1s ease !important",
                        "cursor": "pointer !important",
                    },
                    "&:hover .rt-SliderThumb": {
                        "opacity": "1 !important"
                    },
                    "&:hover .rt-SliderRange": {
                        "background-color": "var(--accent-9) !important", 
                    }
                }
            ),
            rx.text(State.formatted_duration, size="1", color="gray", width="40px"),
            width="100%",
            spacing="4",
            align_items="center",
        ),
        align_items="center",
        width="100%",
    )

def player_bar():
    return rx.cond(
        State.current_track.url != "",
        rx.box(
            rx.hstack(
                # Left: Track Info
                rx.hstack(
                    rx.vstack(
                        rx.text(State.current_track.title, font_weight="bold", size="3"),
                        rx.text(State.current_track.artist, size="2", color="gray"),
                        align_items="start",
                        width="200px",
                    ),
                ),
                rx.spacer(),
                
                # Middle: Playback Controls & Scrubber
                player_controls(),
                rx.spacer(),
                
                # Right: Volume Control
                rx.hstack(
                    rx.icon(tag="volume_2", size=18, color="gray"),
                    rx.slider(
                        default_value=[100], 
                        min=0, max=100, 
                        on_value_commit=State.set_volume, 
                        width="100px"
                    ),
                    width="200px",
                    justify="end",
                ),
                width="100%",
                align_items="center",
            ),
            position="fixed",
            bottom="0",
            width="100%",
            padding="1em 2em",
            margin_bottom="1em",
            background="rgba(10, 10, 10, 0.9)",
            backdrop_filter="blur(20px)",
            border_top="1px solid rgba(255,255,255,0.08)",
        )
    )
