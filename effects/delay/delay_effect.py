import numpy as np
from ..base_effect import AudioEffect
from time import time

class DelayEffect(AudioEffect):
    def __init__(self, sample_rate=44100, delay_time=0.3, feedback=0.3, mix=0.5):
        super().__init__(sample_rate)
        self.delay_time = delay_time  # Delay time in seconds
        self.feedback = feedback  # Feedback amount (0 to 1)
        self.mix = mix  # Wet/dry mix (0 to 1)
        self.buffer_size = int(sample_rate * delay_time)
        self.buffer = np.zeros(self.buffer_size)
        self.buffer_index = 0
        
        # Tap tempo variables
        self.tap_times = []
        self.max_tap_memory = 4  # Remember last 4 taps
        self.last_tap_time = 0
        self.tap_timeout = 2.0  # Reset tap memory after 2 seconds

    def tap_tempo(self):
        """Handle a tap tempo button press"""
        current_time = time()
        
        # If it's been too long since last tap, reset
        if current_time - self.last_tap_time > self.tap_timeout:
            self.tap_times = []
        
        # Add new tap time
        self.tap_times.append(current_time)
        self.last_tap_time = current_time
        
        # Keep only recent taps
        if len(self.tap_times) > self.max_tap_memory:
            self.tap_times = self.tap_times[-self.max_tap_memory:]
        
        # Calculate new delay time if we have enough taps
        if len(self.tap_times) >= 2:
            # Calculate average interval between taps
            intervals = [self.tap_times[i] - self.tap_times[i-1] 
                        for i in range(1, len(self.tap_times))]
            new_delay_time = sum(intervals) / len(intervals)
            
            # Update delay time and buffer
            self.set_delay_time(new_delay_time)
    
    def set_delay_time(self, delay_time):
        """Update delay time and resize buffer if necessary"""
        self.delay_time = delay_time
        new_buffer_size = int(self.sample_rate * delay_time)
        
        if new_buffer_size != self.buffer_size:
            # Create new buffer with new size
            new_buffer = np.zeros(new_buffer_size)
            # Copy old buffer content if possible
            copy_size = min(self.buffer_size, new_buffer_size)
            new_buffer[:copy_size] = self.buffer[:copy_size]
            
            self.buffer = new_buffer
            self.buffer_size = new_buffer_size
            self.buffer_index = min(self.buffer_index, new_buffer_size - 1)

    def _process_impl(self, audio_data):
        # Convert input to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        output = np.zeros_like(audio_data)
        for i in range(len(audio_data)):
            # Get the delayed sample
            delayed_sample = self.buffer[self.buffer_index]
            
            # Calculate new sample with feedback
            new_sample = audio_data[i] + self.feedback * delayed_sample
            
            # Update buffer
            self.buffer[self.buffer_index] = new_sample
            
            # Mix dry and wet signals
            output[i] = (1 - self.mix) * audio_data[i] + self.mix * delayed_sample
            
            # Update buffer index
            self.buffer_index = (self.buffer_index + 1) % self.buffer_size

        return output

    def reset(self):
        self.buffer.fill(0)
        self.buffer_index = 0
        self.tap_times = []
        self.last_tap_time = 0