import reflex as rx
from ..state.base import State

def settings_view():
    return rx.box(
        # Overlay backdrop (blurred background)
        rx.box(
            on_click=State.toggle_settings,
            style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "width": "100vw",
                "height": "100vh",
                "background": "rgba(0, 0, 0, 0.4)",
                "backdrop-filter": "blur(8px)",
                "z-index": 1000,
                "transition": "all 0.3s ease-in-out",
                "opacity": rx.cond(State.show_settings, "1", "0"),
                "pointer-events": rx.cond(State.show_settings, "auto", "none"),
            }
        ),
        
        # Side Window (Sidebar)
        rx.vstack(
            rx.hstack(
                rx.icon(tag="settings", size=24, color="var(--accent-9)"),
                rx.heading("Settings", size="5"),
                rx.spacer(),
                rx.button(
                    rx.icon(tag="x"),
                    on_click=State.toggle_settings,
                    variant="ghost",
                    size="1",
                ),
                width="100%",
                spacing="3",
                align_items="center",
                padding_bottom="1em",
                border_bottom="1px solid var(--gray-4)",
            ),
            
            # Library Settings
            rx.vstack(
                rx.text("Library Settings", size="3", font_weight="bold"),
                rx.vstack(
                    rx.text("Music Directory", size="1", color="gray"),
                    rx.text(
                        rx.cond(State.library_directory != "", State.library_directory, "Default Music Folder"), 
                        size="2", 
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                        width="100%"
                    ),
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="folder_search", size=16),
                            "Select Folder",
                            on_click=State.select_library_directory,
                            variant="solid",
                            color_scheme="blue",
                            size="1",
                            flex="1",
                            cursor="pointer",
                        ),
                        rx.button(
                            "Reset",
                            on_click=lambda: State.set_library_directory(""),
                            variant="soft",
                            size="1",
                            width="80px",
                            cursor="pointer",
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    width="100%",
                    align_items="start",
                    spacing="2",
                    padding="1em",
                    background="var(--gray-3)",
                    border_radius="12px",
                ),
                width="100%",
                align_items="start",
                spacing="3",
                padding_y="1em",
            ),
            
            rx.divider(width="100%"),
            
            # Appearance
            rx.vstack(
                rx.text("Appearance", size="3", font_weight="bold"),
                rx.hstack(
                    rx.text("Dark Mode", size="2"),
                    rx.spacer(),
                    rx.switch(
                        checked=rx.color_mode == "dark",
                        on_change=rx.toggle_color_mode,
                        size="1"
                    ),
                    width="100%",
                    padding="0.8em",
                    background="var(--gray-3)",
                    border_radius="12px",
                ),
                width="100%",
                align_items="start",
                spacing="3",
                padding_y="1em",
            ),
            
            rx.divider(width="100%"),
            
            # Database Management
            rx.vstack(
                rx.text("Storage", size="3", font_weight="bold"),
                rx.vstack(
                    rx.text("Clears all indexed tracks from the storage. Use this if your library becomes desynced.", size="1", color="gray"),
                    rx.button(
                        rx.icon(tag="trash_2", size=16),
                        "Reset Library Storage",
                        on_click=State.reset_database,
                        variant="soft",
                        color_scheme="red",
                        size="2",
                        width="100%",
                        cursor="pointer",
                    ),
                    width="100%",
                    align_items="start",
                    spacing="3",
                    padding="1em",
                    background="var(--gray-3)",
                    border_radius="12px",
                ),
                width="100%",
                align_items="start",
                spacing="3",
                padding_y="1em",
            ),
            
            rx.spacer(),
            
            rx.button(
                "Close Settings",
                on_click=State.toggle_settings,
                size="2",
                variant="solid",
                width="100%",
                cursor="pointer",
            ),
            
            style={
                "position": "fixed",
                "top": "1rem",
                "right": rx.cond(State.show_settings, "1rem", "-450px"),
                "width": "400px",
                "max-width": "calc(100vw - 2rem)",
                "height": "calc(100vh - 2rem)",
                "background": "var(--gray-2)",
                "padding": "2em",
                "border_radius": "24px",
                "box_shadow": "0 20px 60px rgba(0,0,0,0.3)",
                "z-index": 1001,
                "transition": "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                "border": "1px solid var(--gray-4)",
                "backdrop-filter": "blur(20px)",
            },
            spacing="4",
        ),
    )
