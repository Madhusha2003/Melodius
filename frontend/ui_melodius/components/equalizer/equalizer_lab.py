import reflex as rx
import json
import os

from ...state.constants import DATA_FILE

PRESETS: dict[str, list[int]] = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0],
    "Rock": [4, 3, -2, -3, -1, 1, 3, 4],
    "Pop": [-1, 2, 3, 4, 1, -1, -2, -1],
    "Jazz": [3, 2, 1, 3, -1, -1, 0, 1],
    "Classical": [4, 3, 2, 2, -1, -1, -1, 1],
    "Dance": [5, 4, 1, 0, 2, 4, 4, 0],
    "Bass Boost": [6, 5, 4, 2, 0, 0, 0, 0],
    "Vocal Boost": [-2, -3, -3, 1, 4, 4, 2, -1],
    "Electronic": [4, 3, 1, 0, 2, 3, 4, 3],
}

FREQ_MAP = {
    8: [64, 125, 250, 500, 1000, 2000, 4000, 8000],
    12: [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000, 20000],
    16: [31, 63, 100, 160, 250, 400, 630, 1000, 1600, 2500, 4000, 6300, 10000, 12500, 16000, 20000]
}

def interpolate_bands(old_bands: list[int], new_count: int) -> list[int]:
    if not old_bands:
        return [0] * new_count
    if len(old_bands) == new_count:
        return old_bands
    
    new_bands = []
    for i in range(new_count):
        if new_count > 1:
            pos = i * (len(old_bands) - 1) / (new_count - 1)
        else:
            pos = 0
            
        idx = int(pos)
        frac = pos - idx
        if idx >= len(old_bands) - 1:
            new_bands.append(old_bands[-1])
        else:
            val = old_bands[idx] * (1 - frac) + old_bands[idx+1] * frac
            new_bands.append(round(val))
    return new_bands

def format_freq(freq: int) -> str:
    if freq >= 1000:
        return f"{freq/1000:g}kHz"
    return f"{freq}Hz"

FREQ_MAP = {
    8: [64, 125, 250, 500, 1000, 2000, 4000, 8000],
    12: [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000, 20000],
    16: [31, 63, 100, 160, 250, 400, 630, 1000, 1600, 2500, 4000, 6300, 10000, 12500, 16000, 20000]
}

def interpolate_bands(old_bands: list[int], new_count: int) -> list[int]:
    if not old_bands:
        return [0] * new_count
    if len(old_bands) == new_count:
        return old_bands
    
    new_bands = []
    for i in range(new_count):
        if new_count > 1:
            pos = i * (len(old_bands) - 1) / (new_count - 1)
        else:
            pos = 0
            
        idx = int(pos)
        frac = pos - idx
        if idx >= len(old_bands) - 1:
            new_bands.append(old_bands[-1])
        else:
            val = old_bands[idx] * (1 - frac) + old_bands[idx+1] * frac
            new_bands.append(round(val))
    return new_bands

def format_freq(freq: int) -> str:
    if freq >= 1000:
        return f"{freq/1000:g}kHz"
    return f"{freq}Hz"

PRESET_OPTIONS = list(PRESETS.keys()) + ["Custom"]

class EqualizerState(rx.State):
    """Handles the Web Audio API Equalizer directly connected to the React Player."""
    eq_mode: str = "8"
    bands: list[int] = [0, 0, 0, 0, 0, 0, 0, 0]
    frequencies: list[str] = [format_freq(f) for f in FREQ_MAP[8]]
    
    # Advanced features
    bass_boost: int = 0
    clarity: int = 0
    virtualizer: int = 0
    loudness: int = 0
    
    is_eq_initialized: bool = False
    is_eq_active: bool = False

    selected_preset: str = "Flat"

    def reload_eq(self):
        self.is_eq_initialized = False
        
    def load_eq_data(self):
        """Loads data from JSON file on boot."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    eq_data = data.get("eq_lab", {})
                    
                    self.eq_mode = str(eq_data.get("eq_mode", "8"))
                    int_mode = int(self.eq_mode)
                    self.frequencies = [format_freq(f) for f in FREQ_MAP.get(int_mode, FREQ_MAP[8])]
                    
                    saved_bands = eq_data.get("bands")
                    
                    if saved_bands and isinstance(saved_bands, list):
                        self.bands = saved_bands
                    else:
                        # Fallback/Migration for old 8-band structure
                        self.bands = [
                            eq_data.get("band_64", 0),
                            eq_data.get("band_125", 0),
                            eq_data.get("band_250", 0),
                            eq_data.get("band_500", 0),
                            eq_data.get("band_1k", 0),
                            eq_data.get("band_2k", 0),
                            eq_data.get("band_4k", 0),
                            eq_data.get("band_8k", 0)
                        ]
                        # If mode was changed to something else, interpolate the migrated bands
                        if int_mode != 8:
                            self.bands = interpolate_bands(self.bands, int_mode)
                    
                    self.bass_boost = eq_data.get("bass_boost", 0)
                    self.clarity = eq_data.get("clarity", 0)
                    self.virtualizer = eq_data.get("virtualizer", 0)
                    self.loudness = eq_data.get("loudness", 0)
                    self.is_eq_active = eq_data.get("is_active", False)
                    self.selected_preset = eq_data.get("selected_preset", "Flat")
            except Exception as e:
                print("Error loading EQ data:", e)
                
    def save_eq_data(self):
        """Saves current state to JSON."""
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            except:
                pass
                
        data["eq_lab"] = {
            "eq_mode": self.eq_mode,
            "bands": self.bands,
            "bass_boost": self.bass_boost, "clarity": self.clarity, "virtualizer": self.virtualizer, "loudness": self.loudness,
            "is_active": self.is_eq_active,
            "selected_preset": self.selected_preset
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def change_mode(self, mode: str | list[str]):
        if isinstance(mode, list):
            mode = mode[0] if mode else "8"
        if mode == self.eq_mode:
            return
            
        new_mode_int = int(mode)
        # Interpolate current settings to new band count to keep the curve
        self.bands = interpolate_bands(self.bands, new_mode_int)
        self.eq_mode = mode
        self.frequencies = [format_freq(f) for f in FREQ_MAP[new_mode_int]]
        self.is_eq_initialized = False # Force re-init of JS engine with new frequencies
        self.save_eq_data()
        
        # If active, we need to re-initialize the audio context with new filters
        if self.is_eq_active:
            return self.initialize_engine()

    def update_advanced(self, value: list[int], knob_type: str):
        val = value[0] if isinstance(value, list) else value
        if knob_type == "bass":
            self.bass_boost = val
        elif knob_type == "clarity":
            self.clarity = val
        elif knob_type == "virtualizer":
            self.virtualizer = val
        elif knob_type == "loudness":
            self.loudness = val
            
        # Save to user_data.json
        self.save_eq_data()
            
        # Send update to JS Audio engine
        return rx.call_script(f"if (window.updateAdvanced) window.updateAdvanced('{knob_type}', {val});")

    def update_band(self, value: list[int], band_idx: int):
        val = value[0] if isinstance(value, list) else value
        if 0 <= band_idx < len(self.bands):
            self.bands[band_idx] = val
            
        # If user moves a slider manually, set preset to Custom
        self.selected_preset = "Custom"
            
        # Save to user_data.json
        self.save_eq_data()
        
        # We send JS to update the filter immediately
        return rx.call_script(f"if (window.updateEQ) window.updateEQ({band_idx}, {val});")

    def apply_preset(self, preset_name: str):
        if preset_name not in PRESETS:
            return
            
        self.selected_preset = preset_name
        base_values = PRESETS[preset_name]
        
        # Adapt 8-band preset to current mode
        self.bands = interpolate_bands(base_values, int(self.eq_mode))
        
        self.save_eq_data()
        
        # Batch update JS
        js_calls = []
        for i, val in enumerate(self.bands):
            js_calls.append(f"if (window.updateEQ) window.updateEQ({i}, {val});")
            
        return rx.call_script("\n".join(js_calls))

    def apply_eq(self):
        """Called automatically after reload to apply previous states without user interaction."""
        self.load_eq_data()
        if self.is_eq_active :
            self.is_eq_initialized = False

    def initialize_engine(self):
        """Injects the JS Audio Context and sets initial values from saved state."""
        if self.is_eq_initialized or not self.is_eq_active:
            return
            
        self.is_eq_initialized = True
        
        freqs = FREQ_MAP.get(self.eq_mode, FREQ_MAP[8])
        
        init_state_js = f"""
            window.savedEqState = {{
                bands: {self.bands},
                bass: {self.bass_boost},
                clarity: {self.clarity},
                virtualizer: {self.virtualizer},
                loudness: {self.loudness}
            }};
        """
        
        main_script = f"""
            console.log('init_equalizer triggered');
            var p = document.getElementById('audio-player');
            if (p) {{
                // Check if already initialized to avoid multiple MediaElementSources
                if (!window.audioContext) {{
                    try {{
                        // Turn on cross origin
                        p.crossOrigin = "anonymous";
                        
                        window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        window.source = window.audioContext.createMediaElementSource(p);
                        
                        window.filters = [];
                        // Using dynamic band frequencies
                        var freqs = {freqs};
                        var lastNode = window.source;
                        
                        for (var i=0; i<freqs.length; i++) {{
                            var filter = window.audioContext.createBiquadFilter();
                            filter.type = 'peaking';
                            filter.frequency.value = freqs[i];
                            filter.Q.value = {1.41 if self.eq_mode == 8 else 2.0 if self.eq_mode == 12 else 2.8}; // Sharper bandwidth for more bands
                            filter.gain.value = 0; // Flat initially
                            window.filters.push(filter);
                            
                            lastNode.connect(filter);
                            lastNode = filter;
                        }}

                        // ADVANCED FX NODES
                        window.bassNode = window.audioContext.createBiquadFilter();
                        window.bassNode.type = 'peaking';
                        window.bassNode.frequency.value = 80; 
                        window.bassNode.Q.value = 0.7; 
                        window.bassNode.gain.value = 0;
                        
                        window.vocalDipNode = window.audioContext.createBiquadFilter();
                        window.vocalDipNode.type = 'peaking';
                        window.vocalDipNode.frequency.value = 250;
                        window.vocalDipNode.Q.value = 0.5;
                        window.vocalDipNode.gain.value = 0;

                        window.clarityNode = window.audioContext.createBiquadFilter();
                        window.clarityNode.type = 'highshelf';
                        window.clarityNode.frequency.value = 5000;
                        window.clarityNode.gain.value = 0;

                        var sampleRate = window.audioContext.sampleRate;
                        var length = sampleRate * 1.5;
                        var impulse = window.audioContext.createBuffer(2, length, sampleRate);
                        for (var c = 0; c < 2; c++) {{
                            var channelData = impulse.getChannelData(c);
                            for (var i = 0; i < length; i++) {{
                                channelData[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 3.0);
                            }}
                        }}
                        window.convolver = window.audioContext.createConvolver();
                        window.convolver.buffer = impulse;
                        window.wetGain = window.audioContext.createGain();
                        window.wetGain.gain.value = 0;
                        window.dryGain = window.audioContext.createGain();
                        window.dryGain.gain.value = 1;

                        window.compressor = window.audioContext.createDynamicsCompressor();
                        window.compressor.threshold.value = -3;
                        window.compressor.knee.value = 10;
                        window.compressor.ratio.value = 12;
                        window.compressor.attack.value = 0;
                        window.compressor.release.value = 0.25;
                        window.makeupGain = window.audioContext.createGain();
                        window.makeupGain.gain.value = 1;

                        // CONNECT SIGNAL GRAPH
                        window.source.connect(window.bassNode);
                        window.bassNode.connect(window.vocalDipNode);
                        window.vocalDipNode.connect(window.filters[0]);
                        window.filters[window.filters.length - 1].connect(window.clarityNode);
                        
                        window.clarityNode.connect(window.dryGain);
                        window.clarityNode.connect(window.convolver);
                        window.convolver.connect(window.wetGain);

                        window.dryGain.connect(window.compressor);
                        window.wetGain.connect(window.compressor);

                        window.compressor.connect(window.makeupGain);
                        window.makeupGain.connect(window.audioContext.destination);

                        window.updateEQ = function(idx, val) {{
                            if (window.filters && window.filters[idx]) {{
                                window.filters[idx].gain.value = val;
                            }}
                        }};
                        
                        window.updateAdvanced = function(type, val) {{
                            if (!window.audioContext || !window.source) return;
                            if (type === 'bass') {{
                                window.bassNode.gain.value = (val / 100) * 16; 
                                window.vocalDipNode.gain.value = -(val / 100) * 3;
                            }} else if (type === 'clarity') {{
                                window.clarityNode.gain.value = (val / 100) * 12;
                            }} else if (type === 'virtualizer') {{
                                window.wetGain.gain.value = (val / 100) * 0.8;
                                window.dryGain.gain.value = 1 - ((val / 100) * 0.3);
                            }} else if (type === 'loudness') {{
                                window.compressor.threshold.value = -3 - ((val / 100) * 21);
                                window.makeupGain.gain.value = 1 + ((val / 100) * 3);
                            }}
                        }};

                        window.toggleEQ = function(isActive) {{
                            if (!window.audioContext || !window.source) return;
                            window.source.disconnect();
                            if (isActive) {{
                                window.source.connect(window.bassNode);
                            }} else {{
                                window.source.connect(window.audioContext.destination);
                            }}
                        }};
                        
                        if (window.savedEqState) {{
                            for (var i=0; i<window.filters.length; i++) {{
                                window.updateEQ(i, window.savedEqState.bands[i]);
                            }}
                            window.updateAdvanced('bass', window.savedEqState.bass);
                            window.updateAdvanced('clarity', window.savedEqState.clarity);
                            window.updateAdvanced('virtualizer', window.savedEqState.virtualizer);
                            window.updateAdvanced('loudness', window.savedEqState.loudness);
                        }}
                        
                        console.log('Equalizer Web Audio API initialized successfully with saved state!');
                    }} catch(e) {{
                        console.error('Failed to initialize AudioContext:', e);
                    }}
                }} 
                
                if (window.audioContext && window.audioContext.state === 'suspended') {{
                    window.audioContext.resume();
                    console.log('AudioContext resumed');
                }}
            }} else {{
                console.error('Could not find element with id audio-player');
            }}
        """
        
        return rx.call_script(init_state_js + main_script)
        
        # Combine init_state_js with main_script
        return rx.call_script(init_state_js + main_script)

            
    def toggle_eq(self):
        self.is_eq_active = not self.is_eq_active
        self.save_eq_data()
        
        if not self.is_eq_initialized:
            return self.initialize_engine()
        else:
            js_bool = 'true' if self.is_eq_active else 'false'
            return rx.call_script(f"if (window.toggleEQ) window.toggleEQ({js_bool});")

def eq_slider(freq_name: str, band_idx: int) -> rx.Component:
    return rx.vstack(
        rx.text(EqualizerState.bands[band_idx], size="1", font_weight="bold", color="var(--accent-11)"),
        rx.slider(
            value=[EqualizerState.bands[band_idx]],
            min=-12,
            max=12,
            orientation="vertical",
            on_change=lambda v: EqualizerState.update_band(v, band_idx),
            on_value_commit=lambda v: EqualizerState.update_band(v, band_idx),
            height="140px",
            color_scheme="blue",
            cursor="pointer"
        ),
        rx.text(freq_name, size="1", color="gray", font_weight="bold", white_space="nowrap"),
        align_items="center",
        spacing="2",
        width="45px",
        flex_shrink="0",
    )

def round_knob(state_val: int, name: str, update_action):
    return rx.vstack(
        rx.box(
            # The visual dial
            rx.box(
                # The dot indicator
                rx.box(
                    width="6px", height="6px", 
                    bg="var(--accent-9)", 
                    border_radius="50%",
                    position="absolute",
                    top="5px", left="50%",
                    transform="translateX(-50%)"
                ),
                width="100%", height="100%",
                border_radius="50%",
                bg="var(--gray-3)",
                border="2px solid var(--gray-5)",
                box_shadow="inset 0 2px 4px rgba(0,0,0,0.5), 0 2px 5px rgba(0,0,0,0.5)",
                # Use CSS calc to map 0-100 to -135deg to +135deg dynamically based on the rx.Var state
                transform=f"rotate(calc({state_val} * 2.7deg - 135deg))",
                transition="transform 0.1s ease",
            ),
            # The invisible interactive slider mapped perfectly over the circle
            rx.slider(
                value=[state_val],
                min=0, max=100,
                orientation="vertical",
                on_change=update_action,
                on_value_commit=update_action,
                position="absolute",
                top="0", left="0",
                width="100%", height="100%",
                opacity="0", 
                cursor="ns-resize",
                z_index="10" 
            ),
            position="relative",
            width="50px", height="50px",
        ),
        rx.text(name, size="1", color="gray", font_weight="bold"),
        rx.text(f"{state_val}%", size="1", font_weight="bold", color="var(--accent-11)"),
        align_items="center",
        spacing="1"
    )

def equalizer_ui() -> rx.Component:
    return rx.box(
        rx.vstack(
            # HEADER
            rx.hstack(
                rx.icon(tag="sliders-horizontal", size=20, color="var(--accent-9)"),
                rx.text("Equalizer & Effects", font_weight="bold", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon(tag="power", size=15),
                    "EQ " + rx.cond(EqualizerState.is_eq_active, "On", "Off"),
                    on_click=EqualizerState.toggle_eq,
                    size="2",
                    variant=rx.cond(EqualizerState.is_eq_active, "solid", "soft"),
                    color_scheme=rx.cond(EqualizerState.is_eq_active, "green", "gray"),
                    radius="full",
                    cursor="pointer",
                    transition="all 0.2s ease"
                ),
                width="100%",
                align_items="center",
                justify="between",
                padding_bottom="0.8em",
                border_bottom="1px solid var(--gray-4)",
                margin_bottom="0.8em"
            ),
            
            # CONTROL BAR (MODE & PRESET)
            rx.hstack(
    # Left side (Bands)
    rx.hstack(
        rx.text(
            "Bands",
            size="1",
            color="gray",
            font_weight="bold",
        ),
        rx.select(
            items=["8", "12", "16"],
            value=EqualizerState.eq_mode,
            on_change=EqualizerState.change_mode,
            size="1",
            width="70px",
        ),
        align_items="center",   # 👈 vertical center
        spacing="2",
    ),

    rx.spacer(),

    # Right side (Preset)
    rx.hstack(
        rx.text(
            "Preset",
            size="1",
            color="gray",
            font_weight="bold",
        ),
        rx.select(
            items=PRESET_OPTIONS,
            value=EqualizerState.selected_preset,
            on_change=EqualizerState.apply_preset,
            size="2",
            width="140px",
        ),
        align_items="center",   # 👈 vertical center
        spacing="2",
    ),

    width="100%",
    align_items="center",       # 👈 main vertical alignment
    justify_content="space-between",
    margin_bottom="0.5em",
    padding_x="1em",
),
            # DYNAMIC EQ SLIDERS
            rx.box(
                rx.hstack(
                    rx.foreach(
                        EqualizerState.bands,
                        lambda val, idx: eq_slider(EqualizerState.frequencies[idx], idx)
                    ),
                    spacing="2",
                    justify="start",
                    width="auto",
                    padding_x="1em",
                ),
                width="100%",
                overflow_x="scroll",
                padding_bottom="1.5em",
                css={
                    "&::-webkit-scrollbar": {"height": "6px"},
                    "&::-webkit-scrollbar-track": {"background": "transparent"},
                    "&::-webkit-scrollbar-thumb": {"background": "var(--gray-6)", "border-radius": "10px"}
                }
            ),

            rx.divider(margin_y="1em", width="100%", bg="var(--gray-4)"),

            # ADVANCED EFFECTS (ROUND KNOBS)
            rx.hstack(
                round_knob(EqualizerState.bass_boost, "Bass", lambda v: EqualizerState.update_advanced(v, "bass")),
                round_knob(EqualizerState.clarity, "Clarity", lambda v: EqualizerState.update_advanced(v, "clarity")),
                round_knob(EqualizerState.virtualizer, "Virtualizer", lambda v: EqualizerState.update_advanced(v, "virtualizer")),
                round_knob(EqualizerState.loudness, "Loudness", lambda v: EqualizerState.update_advanced(v, "loudness")),
                justify="center",
                spacing="8",
                width="100%",
            ),

            width="100%",
            height="100%",
            align_items="stretch",
            spacing="1",
            overflow_y="auto",
            padding_bottom="0.5em"
        ),
        width="100%",
        height="100%",
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
    )
