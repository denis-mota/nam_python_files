import numpy as np
from ..base_effect import AudioEffect

class DriveEffect(AudioEffect):
    def __init__(self, sample_rate=44100, drive=5.0, tone=0.2, level=1.0):
        super().__init__(sample_rate)
        self.drive = drive  # Drive amount (1.0 to 10.0)
        self.tone = tone   # Tone control (0.0 to 1.0)
        self.level = level # Output level (0.0 to 1.0)

    def _process_impl(self, audio_data):
        # Convert input to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Apply drive
        driven = np.tanh(audio_data * self.drive)

        # Apply tone control (simple low-pass filter)
        output = np.zeros_like(driven)
        last_sample = 0
        for i in range(len(driven)):
            # Mix between raw and filtered signal based on tone control
            filtered = last_sample * self.tone + driven[i] * (1 - self.tone)
            output[i] = filtered
            last_sample = filtered

        # Apply output level
        output *= self.level

        # Ensure the output is within [-1, 1] range
        return np.clip(output, -1, 1)

    def reset(self):
        pass  # No internal state to reset