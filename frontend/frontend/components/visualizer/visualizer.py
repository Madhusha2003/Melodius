import reflex as rx

class VisualizerState(rx.State):
    is_visualizer_active: bool = False
    is_visualizer_initialized: bool = False

    def reload_eq(self):
        self.is_visualizer_initialized = False

    def toggle_visualizer(self):
        self.is_visualizer_active = not self.is_visualizer_active
        
        if not self.is_visualizer_initialized:
            self.is_visualizer_initialized = True
            script = """
            console.log('init_visualizer triggered');
            var canvas = document.getElementById('audio-visualizer-canvas');
            var p = document.getElementById('audio-player');
            
            if (canvas && p) {
                // We share the AudioContext with the Equalizer.
                if (!window.audioContext) {
                    try {
                        p.crossOrigin = "anonymous";
                        window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    } catch(e) {
                         console.error('Failed to initialize AudioContext in visualizer:', e);
                    }
                }
                if (!window.source) {
                    window.source = window.audioContext.createMediaElementSource(p);
                    window.isSourceDirect = true;
                    // Connect directly to destination if EQ isn't taking over
                    window.source.connect(window.audioContext.destination);
                }
                
                if (window.audioContext && window.source && !window.analyser) {
                   window.analyser = window.audioContext.createAnalyser();
                   
                   // Important! We need to connect the analyser without breaking the EQ chain.
                   // The best way is to tap off the source in parallel.
                   window.source.connect(window.analyser);
                   
                   window.analyser.fftSize = 256;
                   window.bufferLength = window.analyser.frequencyBinCount;
                   window.dataArray = new Uint8Array(window.bufferLength);
                   
                   window.drawVisualizer = function() {
                       var canvas = document.getElementById('audio-visualizer-canvas');
                       if (!canvas) return;
                       var ctx = canvas.getContext('2d');
                       
                       if (!window.isVisualizerActive) {
                           // Clear canvas and stop looping when inactive
                           ctx.clearRect(0, 0, canvas.width, canvas.height);
                           return;
                       }
                       
                       requestAnimationFrame(window.drawVisualizer);
                       
                       window.analyser.getByteFrequencyData(window.dataArray);
                       
                       // Fade effect for trails
                       ctx.fillStyle = 'rgba(20, 20, 20, 0.2)';
                       ctx.fillRect(0, 0, canvas.width, canvas.height);
                       
                       var barWidth = (canvas.width / window.bufferLength) * 2.5;
                       var barHeight;
                       var x = 0;
                       
                       for(var i = 0; i < window.bufferLength; i++) {
                           barHeight = window.dataArray[i];
                           
                           // Gradient coloring
                           var r = barHeight + (25 * (i/window.bufferLength));
                           var g = 250 * (i/window.bufferLength);
                           var b = 50;
                           
                           ctx.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
                           ctx.fillRect(x, canvas.height - barHeight / 2, barWidth, barHeight / 2);
                           
                           x += barWidth + 1;
                       }
                   };
                   
                   console.log('Visualizer initialized!');
                }
                
                if (window.audioContext && window.audioContext.state === 'suspended') {
                    window.audioContext.resume();
                }
                
                window.isVisualizerActive = true;
                if (window.drawVisualizer) window.drawVisualizer();

            } else {
                console.error('Could not find canvas or audio-player');
            }
            """
            return rx.call_script(script)
        else:
            js_bool = 'true' if self.is_visualizer_active else 'false'
            script = f"""
            window.isVisualizerActive = {js_bool};
            if ({js_bool} && window.drawVisualizer && window.audioContext && window.audioContext.state !== 'suspended') {{
                window.drawVisualizer();
            }} else if (!{js_bool}) {{
                 var canvas = document.getElementById('audio-visualizer-canvas');
                 if(canvas){{
                    var ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                 }}
            }}
            """
            return rx.call_script(script)

def visualizer_ui() -> rx.Component:
    return rx.box(
        rx.vstack(
            # HEADER
            rx.hstack(
                rx.icon(tag="activity", size=20, color="var(--accent-9)"),
                rx.text("Visualizer", font_weight="bold", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon(tag="power", size=15),
                    "Visualizer " + rx.cond(VisualizerState.is_visualizer_active, "On", "Off"),
                    on_click=VisualizerState.toggle_visualizer,
                    size="2",
                    variant=rx.cond(VisualizerState.is_visualizer_active, "solid", "soft"),
                    color_scheme=rx.cond(VisualizerState.is_visualizer_active, "blue", "gray"),
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
            
            # CANVAS CONTAINER
            rx.box(
                rx.el.canvas(
                    id="audio-visualizer-canvas",
                    width="600",
                    height="150",
                    style={"width": "100%", "height": "100%", "border_radius": "12px", "background": "var(--gray-3)"}
                ),
                width="100%",
                height="150px",
                border_radius="12px",
                overflow="hidden",
                box_shadow="inset 0 2px 10px rgba(0,0,0,0.2)",
            ),
            width="100%",
            align_items="center",
        ),
        width="100%",
        padding="2em",
        border_radius="24px",
        background="var(--gray-2)",
        box_shadow="0 10px 40px rgba(0,0,0,0.1)",
        margin_bottom="1em" # Space between this and EQ if stacked
    )
