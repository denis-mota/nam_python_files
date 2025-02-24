import numpy as np
from ..base_effect import AudioEffect

class ReverbEffect(AudioEffect):
    def __init__(self, sample_rate=44100, room_size=0.5, damping=0.5, mix=0.3):
        super().__init__(sample_rate)
        self.room_size = room_size  # Size of the virtual room (0.0 to 1.0)
        self.damping = damping      # High frequency damping (0.0 to 1.0)
        self.mix = mix              # Wet/dry mix (0.0 to 1.0)
        
        # Initialize delay lines for early reflections and late reverberation
        self.early_delays = [int(sample_rate * t) for t in [0.01, 0.015, 0.02, 0.025]]
        self.late_delays = [int(sample_rate * t) for t in [0.03, 0.035, 0.04, 0.045]]
        
        # Create buffers for each delay line
        self.early_buffers = [np.zeros(delay) for delay in self.early_delays]
        self.late_buffers = [np.zeros(delay) for delay in self.late_delays]
        
        # Buffer indices
        self.early_indices = [0] * len(self.early_delays)
        self.late_indices = [0] * len(self.late_delays)
        
        # Feedback coefficients
        self.early_gains = [0.7, 0.6, 0.5, 0.4]
        self.late_gains = [0.3, 0.25, 0.2, 0.15]

    def _process_impl(self, audio_data):
        # Convert input to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Pre-allocate arrays for better performance
        buffer_size = len(audio_data)
        early_reflections = np.zeros(buffer_size)
        late_reverb = np.zeros(buffer_size)

        # Process early reflections
        for i, (buffer, index, gain) in enumerate(zip(self.early_buffers, self.early_indices, self.early_gains)):
            # Ensure buffer is large enough
            if len(buffer) < buffer_size:
                new_buffer = np.zeros(buffer_size)
                new_buffer[:len(buffer)] = buffer
                self.early_buffers[i] = new_buffer
                buffer = new_buffer

            # Get delayed samples
            indices = np.mod(np.arange(buffer_size) + index, buffer_size)
            early_reflections += buffer[indices] * gain * self.room_size
            
            # Update buffer
            buffer[indices] = audio_data
            self.early_indices[i] = (index + buffer_size) % buffer_size

        # Process late reverberation
        for i, (buffer, index, gain) in enumerate(zip(self.late_buffers, self.late_indices, self.late_gains)):
            # Ensure buffer is large enough
            if len(buffer) < buffer_size:
                new_buffer = np.zeros(buffer_size)
                new_buffer[:len(buffer)] = buffer
                self.late_buffers[i] = new_buffer
                buffer = new_buffer

            # Get delayed samples with damping
            indices = np.mod(np.arange(buffer_size) + index, buffer_size)
            damped = buffer[indices] * (1 - self.damping)
            late_reverb += damped * gain * self.room_size
            
            # Update buffer with input + early reflections feedback
            buffer[indices] = audio_data + early_reflections * 0.5
            self.late_indices[i] = (index + buffer_size) % buffer_size

        # Mix dry and wet signals (vectorized)
        output = (1 - self.mix) * audio_data + self.mix * (early_reflections + late_reverb)

        # Ensure output is within [-1, 1] range and matches input shape
        output = np.clip(output, -1, 1)
        if len(audio_data.shape) > 1:
            output = np.column_stack((output, output))
        return output

    def reset(self):
        # Clear all delay buffers
        for buffer in self.early_buffers:
            buffer.fill(0)
        for buffer in self.late_buffers:
            buffer.fill(0)
        
        # Reset indices
        self.early_indices = [0] * len(self.early_delays)
        self.late_indices = [0] * len(self.late_delays)