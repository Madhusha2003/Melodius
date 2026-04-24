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
                    rx.cond(
                        State.current_track.cover_url,
                        rx.image(
                            src=State.current_track.cover_url,
                            key=State.current_track.url, # Force re-render on track change
                            width="56px",
                            height="56px",
                            border_radius="12px",
                            object_fit="cover",
                            box_shadow="0 4px 12px rgba(0,0,0,0.4)",
                        ),
                        rx.center(
                            rx.icon(tag="music", size=24, color="gray"),
                            width="56px",
                            height="56px",
                            background="var(--gray-3)",
                            border_radius="12px",
                        )
                    ),
                    rx.vstack(
                        # Title Marquee
                        rx.box(
                            rx.text(
                                rx.cond(
                                    State.current_track.title != "",
                                    f"{State.current_track.title} \u00A0\u00A0\u00A0\u00A0\u00A0 {State.current_track.title} \u00A0\u00A0\u00A0\u00A0\u00A0 ",
                                    ""
                                ),
                                font_weight="bold", 
                                size="3", 
                                class_name="marquee-text"
                            ),
                            class_name="marquee-container",
                        ),
                        # Artist Marquee
                        rx.box(
                            rx.text(
                                rx.cond(
                                    State.current_track.artist != "",
                                    f"{State.current_track.artist} \u00A0\u00A0\u00A0\u00A0\u00A0 {State.current_track.artist} \u00A0\u00A0\u00A0\u00A0\u00A0 ",
                                    ""
                                ),
                                size="2", 
                                color="gray",
                                class_name="marquee-text"
                            ),
                            class_name="marquee-container",
                        ),
                        align_items="start",
                        width="250px",
                        spacing="1",
                    ),
                    spacing="4",
                    align_items="center",
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
            width="100%",
            padding="1.5em 3em",
            background=rx.color_mode_cond(
                light="rgba(255, 255, 255, 0.95)",
                dark="rgba(10, 10, 10, 0.95)"
            ),
            border_top="1px solid",
            border_color=rx.color_mode_cond(
                light="rgba(0,0,0,0.1)",
                dark="rgba(255,255,255,0.1)"
            ),
            z_index="100",
        )
    )
