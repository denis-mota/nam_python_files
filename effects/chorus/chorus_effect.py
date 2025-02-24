import numpy as np
from ..base_effect import AudioEffect

class ChorusEffect(AudioEffect):
    def __init__(self, sample_rate=44100, rate=1.0, depth=0.002, mix=0.5):
        super().__init__(sample_rate)
        self.rate = rate  # LFO rate in Hz
        self.depth = depth  # Delay depth in seconds
        self.mix = mix  # Wet/dry mix (0 to 1)
        self.phase = 0
        self.buffer = np.zeros(int(sample_rate * 0.1))  # 100ms buffer
        self.buffer_index = 0

    def _process_impl(self, audio_data):
        # Convert input to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        output = np.zeros_like(audio_data)
        for i in range(len(audio_data)):
            # Update buffer
            self.buffer[self.buffer_index] = audio_data[i]
            
            # Calculate LFO value
            lfo = np.sin(2 * np.pi * self.rate * self.phase / self.sample_rate)
            delay_samples = int((self.depth * self.sample_rate * (lfo + 1)) / 2)
            
            # Get delayed sample
            delay_index = (self.buffer_index - delay_samples) % len(self.buffer)
            delayed_sample = self.buffer[delay_index]
            
            # Mix dry and wet signals
            output[i] = (1 - self.mix) * audio_data[i] + self.mix * delayed_sample
            
            # Update indices
            self.buffer_index = (self.buffer_index + 1) % len(self.buffer)
            self.phase = (self.phase + 1) % self.sample_rate

        return output

    def reset(self):
        self.phase = 0
        self.buffer.fill(0)
        self.buffer_index = 0