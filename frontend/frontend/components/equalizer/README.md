# Melodius Equalizer & Effects Engine

This folder contains the core Web Audio API implementation for the Melodius application. Rather than relying on heavyweight React wrappers, this equalizer uses a direct Javascript bridge from **Reflex** to manipulate the browser's native audio graph.

## 1. Feature Descriptions

### **8-Band Equalizer**
A standard graphic equalizer spanning the frequency spectrum: **64Hz, 125Hz, 250Hz, 500Hz, 1kHz, 2kHz, 4kHz, 8kHz**.
- **How it works**: Uses a cascade of `BiquadFilterNode` elements set to the `'peaking'` type. 
- **Q Value**: Set to `1.41` to provide an overlapping, musical bandwidth between the 8 points, ensuring sweeping the sliders feels natural.

### **Bass Boost & Anti-Masking**
Targets the body of the bass and kick drum without introducing sub-bass distortion or muddying the singers.
- **How it works**: Uses a `'peaking'` filter at **80Hz** with a wide `Q` of **0.7**.
- **Vocal Dip (Anti-Masking)**: Automatically applies a slight volume cut at **250Hz** (the "mud" frequency). When low frequencies are heavily boosted, they tend to "mask" or drown out the midrange vocals. This dip guarantees the singer's voice cuts through the mix even at max bass.

### **Clarity (Exciter)**
Adds "air", "sheen", and high-definition crispness to vocals, cymbals, and synths.
- **How it works**: Uses a `'highshelf'` filter starting at **5000Hz**. Everything above this frequency is gently boosted.

### **Virtualizer (Reverb/Spatializer)**
Creates a wider, 3D room-like stereo spread, making the music feel like it is playing in a concert hall rather than directly inside your headphones.
- **How it works**: Uses a `ConvolverNode`. On initialization, it mathematically generates a 1.5-second impulse response buffer (exponential decay noise). The knob acts as a "Dry/Wet" mix, crossfading the raw audio with the reverberated audio.

### **Loudness (Dynamic Limiter)**
Makes the music sound massively fuller and louder without blowing out your speakers or causing harsh digital distortion.
- **How it works**: Combines a `DynamicsCompressorNode` and a `GainNode` (Make-up Gain). As you turn the dial, it pushes the compressor threshold down (clamping down on volume spikes) while aggressively pushing the base volume up seamlessly.

---

## 2. How to Tweak & Customize (Developer Guide)

If you wish to change how aggressive or subtle these effects are, you need to edit the `window.updateAdvanced` JavaScript function inside `equalizer.py`.

### Tuning the Bass Boost
```javascript
if (type === 'bass') {
    // 1. Change the maximum boost (currently +16dB)
    // To make it hit harder, change 16 to 20. To make it subtle, change to 10.
    window.bassNode.gain.value = (val / 100) * 16; 
    
    // 2. Change the Vocal Dip (currently ducks up to -3dB)
    // To leave more mids, change 3 to 1. To carve it out more, change to 5.
    window.vocalDipNode.gain.value = -(val / 100) * 3;
}
```
*If you want to change the frequency (e.g., target 60Hz instead of 80Hz), look for `window.bassNode.frequency.value = 80;` in the `init_equalizer` script.*

### Tuning Clarity
```javascript
} else if (type === 'clarity') {
    // Change the maximum treble boost (currently +12dB)
    window.clarityNode.gain.value = (val / 100) * 12; 
}
```

### Tuning Virtualizer
```javascript
} else if (type === 'virtualizer') {
    // 1. Wet Gain: How much echo is added (currently hits a max of 0.8 / 80% volume)
    window.wetGain.gain.value = (val / 100) * 0.8;
    
    // 2. Dry Gain: How much the original music ducks out of the way (currently drops to 0.7 / 70% volume)
    window.dryGain.gain.value = 1 - ((val / 100) * 0.3); 
}
```
*If you want a **longer reverb tail** (like a cathedral), find `var length = sampleRate * 1.5;` in the init script and change `1.5` to `3.0`.*

### Tuning Loudness
```javascript
} else if (type === 'loudness') {
    // 1. Threshold: How low the compressor bites. Currently goes from -3dB down to -24dB ( -3 - 21 = -24 )
    window.compressor.threshold.value = -3 - ((val / 100) * 21);
    
    // 2. Makeup Gain: The volume multiplier. Currently multiplies up to 4x ( 1 + 3 = 4 )
    // Warning: Pushing this past 5 or 6 may cause distortion on heavily mastered tracks!
    window.makeupGain.gain.value = 1 + ((val / 100) * 3); 
}
```
