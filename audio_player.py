import sounddevice as sd
import soundfile as sf
import tkinter as tk
from tkinter import filedialog
import numpy as np
import os
import json
import nam_binding

class AudioPlayer:
    def __init__(self):
        self.audio_data = None
        self.sample_rate = 44100  # Standard sample rate for audio
        self.playing = False
        self.stream = None
        self.last_directory = os.path.expanduser('~')
        self.nam_processor = None
        self.input_stream = None
        self.output_stream = None
        self.is_monitoring = False
        self.ir_processor = None

    def is_nam_file(self, file_path):
        return file_path.lower().endswith('.nam')

    def is_ir_file(self, file_path):
        return file_path.lower().endswith('.wav')

    def load_ir_file(self, file_path):
        try:
            self.ir_processor = nam_binding.IRProcessor(file_path, self.sample_rate)
            print(f'IR file loaded: {file_path}')
            return True
        except Exception as e:
            print(f'Error loading IR file: {e}')
            return False

    def load_nam_file(self, file_path):
        try:
            # Load NAM file using C++ implementation
            self.nam_processor = nam_binding.NAMProcessor(file_path)
            self.nam_processor.reset(self.sample_rate, 1024)  # Initialize with current sample rate
            print(f'NAM file loaded: {file_path}')
            return True
        except Exception as e:
            print(f'Error loading NAM file: {e}')
            return False

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a file',
            initialdir=self.last_directory,
            filetypes=[('All Audio Files', '*.wav *.mp3 *.ogg *.nam'), 
                      ('NAM Files', '*.nam'),
                      ('IR Files', '*.wav'),
                      ('Audio Files', '*.mp3 *.ogg'),
                      ('All files', '*.*')]
        )
        if file_path:
            try:
                self.last_directory = os.path.dirname(file_path)
                
                if self.is_nam_file(file_path):
                    return self.load_nam_file(file_path)
                elif self.is_ir_file(file_path):
                    if not hasattr(self, 'audio_data') or self.audio_data is None:
                        return self.load_ir_file(file_path)
                    else:
                        self.audio_data, self.sample_rate = sf.read(file_path)
                        print(f'Audio file loaded: {file_path}')
                        print(f'Sample rate: {self.sample_rate} Hz')
                        return True
                
                self.audio_data, self.sample_rate = sf.read(file_path)
                print(f'Audio file loaded: {file_path}')
                print(f'Sample rate: {self.sample_rate} Hz')
                return True
            except Exception as e:
                print(f'Error loading file: {e}')
                return False
        return False

    def process_audio(self, audio_input):
        try:
            # Process through NAM if available
            if self.nam_processor is not None:
                audio_input = self.nam_processor.process(audio_input.astype(np.float32))

            # Apply IR if available
            if self.ir_processor is not None:
                audio_input = self.ir_processor.process(audio_input)
            
            return audio_input
        except Exception as e:
            print(f'Error in audio processing: {e}')
            return audio_input

    def play(self):
        if self.audio_data is None:
            print('No audio file loaded')
            return

        if self.playing:
            print('Already playing')
            return

        def callback(outdata, frames, time, status):
            if status:
                print(status)
            if len(self.audio_data) > 0:
                if len(self.audio_data.shape) == 1:
                    data = self.audio_data[:frames]
                    self.audio_data = self.audio_data[frames:]
                    outdata[:, 0] = data
                else:
                    data = self.audio_data[:frames]
                    self.audio_data = self.audio_data[frames:]
                    outdata[:] = data
            else:
                self.stop()
                raise sd.CallbackStop()

        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2 if len(self.audio_data.shape) > 1 else 1,
                callback=callback
            )
            self.stream.start()
            self.playing = True
            print('Playing...')
        except Exception as e:
            print(f'Error playing: {e}')

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.playing = False
            print('Playback stopped')
        self.stop_monitoring()

    def start_monitoring(self):
        if self.is_monitoring:
            print('Already monitoring')
            return

        if self.nam_processor is None:
            print('Please load a NAM model first')
            return

        def audio_callback(indata, outdata, frames, time, status):
            if status:
                print(status)

            # Convert input to mono if stereo
            if indata.shape[1] > 1:
                audio_input = np.mean(indata, axis=1)
            else:
                audio_input = indata[:, 0]

            # Process audio through NAM model
            processed_audio = self.process_audio(audio_input)

            # Convert to stereo if needed
            if outdata.shape[1] > 1:
                outdata[:] = np.column_stack((processed_audio, processed_audio))
            else:
                outdata[:, 0] = processed_audio

        try:
            self.input_stream = sd.Stream(
                channels=2,  # Set to stereo output
                samplerate=self.sample_rate,
                blocksize=1024,
                callback=audio_callback,
                dtype=np.float32  # Ensure consistent data type
            )
            self.input_stream.start()
            self.is_monitoring = True
            print('Monitoring started...')
        except Exception as e:
            print(f'Error starting monitoring: {e}')

    def stop_monitoring(self):
        if self.input_stream is not None:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None
            self.is_monitoring = False
            print('Monitoring stopped')

def main():
    root = tk.Tk()
    root.title('Neural Amp Modeler')
    root.geometry('300x300')

    player = AudioPlayer()

    load_nam_button = tk.Button(
        root,
        text='Load NAM Model',
        command=player.load_file
    )
    load_nam_button.pack(pady=10)

    load_ir_button = tk.Button(
        root,
        text='Load IR File',
        command=lambda: player.load_file()
    )
    load_ir_button.pack(pady=10)

    play_button = tk.Button(
        root,
        text='Play File',
        command=player.play
    )
    play_button.pack(pady=10)

    stop_button = tk.Button(
        root,
        text='Stop',
        command=player.stop
    )
    stop_button.pack(pady=10)

    monitor_button = tk.Button(
        root,
        text='Start Guitar Input',
        command=player.start_monitoring
    )
    monitor_button.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()