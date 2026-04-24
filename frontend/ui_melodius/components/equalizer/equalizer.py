import reflex as rx
import json
import os

from ...state.constants import DATA_FILE

class EqualizerState(rx.State):
    """Handles the Web Audio API Equalizer directly connected to the React Player."""
    band_64: int = 0
    band_125: int = 0
    band_250: int = 0
    band_500: int = 0
    band_1k: int = 0
    band_2k: int = 0
    band_4k: int = 0
    band_8k: int = 0
    
    # Advanced features
    bass_boost: int = 0
    clarity: int = 0
    virtualizer: int = 0
    loudness: int = 0
    
    is_eq_initialized: bool = False
    is_eq_active: bool = False

    def reload_eq(self):
        self.is_eq_initialized = False
        
    def load_eq_data(self):
        """Loads data from JSON file on boot."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    eq_data = data.get("eq", {})
                    self.band_64 = eq_data.get("band_64", 0)
                    self.band_125 = eq_data.get("band_125", 0)
                    self.band_250 = eq_data.get("band_250", 0)
                    self.band_500 = eq_data.get("band_500", 0)
                    self.band_1k = eq_data.get("band_1k", 0)
                    self.band_2k = eq_data.get("band_2k", 0)
                    self.band_4k = eq_data.get("band_4k", 0)
                    self.band_8k = eq_data.get("band_8k", 0)
                    
                    self.bass_boost = eq_data.get("bass_boost", 0)
                    self.clarity = eq_data.get("clarity", 0)
                    self.virtualizer = eq_data.get("virtualizer", 0)
                    self.loudness = eq_data.get("loudness", 0)
                    self.is_eq_active = eq_data.get("is_active", False)
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
                
        data["eq"] = {
            "band_64": self.band_64, "band_125": self.band_125, "band_250": self.band_250, "band_500": self.band_500,
            "band_1k": self.band_1k, "band_2k": self.band_2k, "band_4k": self.band_4k, "band_8k": self.band_8k,
            "bass_boost": self.bass_boost, "clarity": self.clarity, "virtualizer": self.virtualizer, "loudness": self.loudness,
            "is_active": self.is_eq_active
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

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
        if band_idx == 0:
            self.band_64 = val
        elif band_idx == 1:
            self.band_125 = val
        elif band_idx == 2:
            self.band_250 = val
        elif band_idx == 3:
            self.band_500 = val
        elif band_idx == 4:
            self.band_1k = val
        elif band_idx == 5:
            self.band_2k = val
        elif band_idx == 6:
            self.band_4k = val
        elif band_idx == 7:
            self.band_8k = val
            
        # Save to user_data.json
        self.save_eq_data()
        
        # We send JS to update the filter immediately
        return rx.call_script(f"if (window.updateEQ) window.updateEQ({band_idx}, {val});")

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
        
        init_state_js = f"""
            window.savedEqState = {{
                bands: [{self.band_64}, {self.band_125}, {self.band_250}, {self.band_500}, {self.band_1k}, {self.band_2k}, {self.band_4k}, {self.band_8k}],
                bass: {self.bass_boost},
                clarity: {self.clarity},
                virtualizer: {self.virtualizer},
                loudness: {self.loudness}
            }};
        """
        
        main_script = """
            console.log('init_equalizer triggered');
            var p = document.getElementById('audio-player');
            if (p) {
                // Check if already initialized to avoid multiple MediaElementSources
                if (!window.audioContext) {
                    try {
                        // Turn on cross origin
                        p.crossOrigin = "anonymous";
                        
                        window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        window.source = window.audioContext.createMediaElementSource(p);
                        
                        window.filters = [];
                        // Using standard 8-band frequencies
                        var freqs = [64, 125, 250, 500, 1000, 2000, 4000, 8000];
                        var lastNode = window.source;
                        
                        for (var i=0; i<freqs.length; i++) {
                            var filter = window.audioContext.createBiquadFilter();
                            filter.type = 'peaking';
                            filter.frequency.value = freqs[i];
                            filter.Q.value = 1.41; // Sharper bandwidth for 8-band
                            filter.gain.value = 0; // Flat initially
                            window.filters.push(filter);
                            
                            lastNode.connect(filter);
                            lastNode = filter;
                        }

                        // ADVANCED FX NODES
                        // 1. Bass Boost Node
                        // Changed from 'lowshelf' to 'peaking' to avoid boosting mud/sub rumbles that distort
                        window.bassNode = window.audioContext.createBiquadFilter();
                        window.bassNode.type = 'peaking';
                        window.bassNode.frequency.value = 80; // Raised slightly to catch more low-end body
                        window.bassNode.Q.value = 0.7; // Widened the curve so it boosts more musical frequencies
                        window.bassNode.gain.value = 0;
                        
                        // 1b. Vocal Dip (Anti-Masking)
                        // When bass gets huge, it "masks" the midrange voices. We dip 250Hz slightly to make room.
                        window.vocalDipNode = window.audioContext.createBiquadFilter();
                        window.vocalDipNode.type = 'peaking';
                        window.vocalDipNode.frequency.value = 250;
                        window.vocalDipNode.Q.value = 0.5;
                        window.vocalDipNode.gain.value = 0;

                        // 2. Clarity (Treble/Presence) Node
                        window.clarityNode = window.audioContext.createBiquadFilter();
                        window.clarityNode.type = 'highshelf';
                        window.clarityNode.frequency.value = 5000;
                        window.clarityNode.gain.value = 0;

                        // 3. Virtualizer (Algorithmic Reverb via Convolver)
                        var sampleRate = window.audioContext.sampleRate;
                        var length = sampleRate * 1.5; // 1.5 second tail
                        var impulse = window.audioContext.createBuffer(2, length, sampleRate);
                        for (var c = 0; c < 2; c++) {
                            var channelData = impulse.getChannelData(c);
                            for (var i = 0; i < length; i++) {
                                // Exponential decay noise for fake room acoustics
                                channelData[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 3.0);
                            }
                        }
                        window.convolver = window.audioContext.createConvolver();
                        window.convolver.buffer = impulse;
                        window.wetGain = window.audioContext.createGain();
                        window.wetGain.gain.value = 0;
                        window.dryGain = window.audioContext.createGain();
                        window.dryGain.gain.value = 1;

                        // 4. Loudness (Compressor & Makeup Gain)
                        window.compressor = window.audioContext.createDynamicsCompressor();
                        window.compressor.threshold.value = -3;
                        window.compressor.knee.value = 10;
                        window.compressor.ratio.value = 12;
                        window.compressor.attack.value = 0;
                        window.compressor.release.value = 0.25;
                        window.makeupGain = window.audioContext.createGain();
                        window.makeupGain.gain.value = 1;

                        // CONNECT SIGNAL GRAPH (Routing)
                        // Source -> Bass -> Vocal Dip -> EQ Array -> Clarity
                        window.source.connect(window.bassNode);
                        window.bassNode.connect(window.vocalDipNode);
                        window.vocalDipNode.connect(window.filters[0]);
                        window.filters[7].connect(window.clarityNode);
                        
                        // Split for Virtualizer (Reverb)
                        window.clarityNode.connect(window.dryGain);
                        window.clarityNode.connect(window.convolver);
                        window.convolver.connect(window.wetGain);

                        // Mix back into Compressor
                        window.dryGain.connect(window.compressor);
                        window.wetGain.connect(window.compressor);

                        // Compressor to Makeup Gain to Speakers
                        window.compressor.connect(window.makeupGain);
                        window.makeupGain.connect(window.audioContext.destination);

                        // Attach EQ parameters update function
                        window.updateEQ = function(idx, val) {
                            if (window.filters && window.filters[idx]) {
                                window.filters[idx].gain.value = val;
                            }
                        };
                        
                        // Attach Advanced FX parameters update function
                        window.updateAdvanced = function(type, val) {
                            if (!window.audioContext || !window.source) return;
                            if (type === 'bass') {
                                // Cap boost to +16dB (a safe, noticeable medium)
                                window.bassNode.gain.value = (val / 100) * 16; 
                                // Dip the muddy vocals dynamically as bass increases (max -3dB) to prevent complete loss
                                window.vocalDipNode.gain.value = -(val / 100) * 3;
                            } else if (type === 'clarity') {
                                window.clarityNode.gain.value = (val / 100) * 12; // Boost up to +12dB
                            } else if (type === 'virtualizer') {
                                window.wetGain.gain.value = (val / 100) * 0.8;
                                window.dryGain.gain.value = 1 - ((val / 100) * 0.3); // Slight dry volume dip 
                            } else if (type === 'loudness') {
                                window.compressor.threshold.value = -3 - ((val / 100) * 21); // Press hard to -24 threshold
                                window.makeupGain.gain.value = 1 + ((val / 100) * 3); // Recover volume x1 up to x4
                            }
                        };

                        // Attach bypass function
                        window.toggleEQ = function(isActive) {
                            if (!window.audioContext || !window.source) return;
                            window.source.disconnect();
                            if (isActive) {
                                // Connect source directly to bass node block to resume chain
                                window.source.connect(window.bassNode);
                            } else {
                                // Bypass EQ entirely, route straight to destination speakers
                                window.source.connect(window.audioContext.destination);
                            }
                        };
                        
                        // --- APPLY INITIAL VALUES IMMEDIATELY ---
                        if (window.savedEqState) {
                            for (var i=0; i<8; i++) {
                                window.updateEQ(i, window.savedEqState.bands[i]);
                            }
                            window.updateAdvanced('bass', window.savedEqState.bass);
                            window.updateAdvanced('clarity', window.savedEqState.clarity);
                            window.updateAdvanced('virtualizer', window.savedEqState.virtualizer);
                            window.updateAdvanced('loudness', window.savedEqState.loudness);

                        }
                        
                        console.log('Equalizer Web Audio API initialized successfully with saved state!');
                    } catch(e) {
                        console.error('Failed to initialize AudioContext:', e);
                    }
                } 
                
                if (window.audioContext && window.audioContext.state === 'suspended') {
                    window.audioContext.resume();
                    console.log('AudioContext resumed');
                }
            } else {
                console.error('Could not find element with id audio-player');
            }
        """
        
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

def eq_slider(name: str, band_idx: int, val: int) -> rx.Component:
    return rx.vstack(
        rx.text(val, size="1", font_weight="bold", color="var(--accent-11)"),
        rx.slider(
            default_value=[val],
            value=[val],
            min=-12,
            max=12,
            orientation="vertical",
            # on_change updates UI text in real-time, on_value_commit fires the final JS to prevent extreme lag
            on_change=lambda v: EqualizerState.update_band(v, band_idx),
            on_value_commit=lambda v: EqualizerState.update_band(v, band_idx),
            height="150px",
            color_scheme="blue",
            cursor="pointer"
        ),
        rx.text(name, size="1", color="gray", font_weight="bold"),
        align_items="center",
        spacing="2"
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
            width="55px", height="55px",
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
                padding_bottom="1em",
                border_bottom="1px solid var(--gray-4)",
                margin_bottom="1em"
            ),
            
            # 8-BAND EQ SLIDERS
            rx.hstack(
                eq_slider("64Hz", 0, EqualizerState.band_64),
                eq_slider("125Hz", 1, EqualizerState.band_125),
                eq_slider("250Hz", 2, EqualizerState.band_250),
                eq_slider("500Hz", 3, EqualizerState.band_500),
                eq_slider("1kHz", 4, EqualizerState.band_1k),
                eq_slider("2kHz", 5, EqualizerState.band_2k),
                eq_slider("4kHz", 6, EqualizerState.band_4k),
                eq_slider("8kHz", 7, EqualizerState.band_8k),
                spacing="4",
                justify="center",
                width="100%"
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
            align_items="center",
            justify="center",
        ),
        width="100%",
        height="100%",
        padding="2.5em",
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
