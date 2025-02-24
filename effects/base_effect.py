import numpy as np

class AudioEffect:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.is_enabled = True

    def process(self, audio_data):
        """Process the audio data through the effect.
        
        Args:
            audio_data (numpy.ndarray): Input audio data
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        if not self.is_enabled:
            return audio_data
        return self._process_impl(audio_data)

    def _process_impl(self, audio_data):
        """Implementation of the effect processing.
        
        This method should be overridden by subclasses.
        
        Args:
            audio_data (numpy.ndarray): Input audio data
            
        Returns:
            numpy.ndarray: Processed audio data
        """
        return audio_data

    def enable(self):
        """Enable the effect."""
        self.is_enabled = True

    def disable(self):
        """Disable the effect."""
        self.is_enabled = False

    def toggle(self):
        """Toggle the effect on/off."""
        self.is_enabled = not self.is_enabled

    def reset(self):
        """Reset the effect's internal state.
        
        This method should be overridden by subclasses if they maintain internal state.
        """
        pass