import sounddevice as sd
import soundfile as sf
import tkinter as tk
from tkinter import filedialog
import numpy as np
import os
import json
import nam_binding
from effects.chorus.chorus_effect import ChorusEffect
from effects.drive.drive_effect import DriveEffect
from effects.delay.delay_effect import DelayEffect
from effects.reverb.reverb_effect import ReverbEffect

class AudioPlayer:
    def __init__(self):
        self.audio_data = None
        self.sample_rate = 44100  # Standard sample rate for audio
        self.playing = False
        self.stream = None
        self.last_directory = os.path.expanduser('~')
        self.effect_chain = []
        self.input_stream = None
        self.output_stream = None
        self.is_monitoring = False
        
        # Initialize effects
        self.chorus = ChorusEffect(self.sample_rate)
        self.drive = DriveEffect(self.sample_rate)
        self.nam_processor = None
        self.ir_processor = None
        self.delay = DelayEffect(self.sample_rate)
        self.reverb = ReverbEffect(self.sample_rate)
        
        # Effect states
        self.effect_states = {
            'chorus': False,
            'drive': False,
            'nam': False,
            'ir': False,
            'delay': False,
            'reverb': False
        }

        # Effect parameters
        self.effect_params = {
            'chorus': {
                'rate': {'value': 1.0, 'min': 0.1, 'max': 5.0, 'label': 'Rate (Hz)'},
                'depth': {'value': 0.002, 'min': 0.0001, 'max': 0.01, 'label': 'Depth (s)'},
                'mix': {'value': 0.5, 'min': 0.0, 'max': 1.0, 'label': 'Mix'}
            },
            'drive': {
                'drive': {'value': 1.0, 'min': 1.0, 'max': 10.0, 'label': 'Drive'},
                'tone': {'value': 0.7, 'min': 0.0, 'max': 1.0, 'label': 'Tone'},
                'level': {'value': 1.0, 'min': 0.0, 'max': 1.0, 'label': 'Level'}
            },
            'delay': {
                'delay_time': {'value': 0.3, 'min': 0.05, 'max': 1.0, 'label': 'Time (s)'},
                'feedback': {'value': 0.3, 'min': 0.0, 'max': 0.9, 'label': 'Feedback'},
                'mix': {'value': 0.5, 'min': 0.0, 'max': 1.0, 'label': 'Mix'}
            },
            'reverb': {
                'room_size': {'value': 0.5, 'min': 0.0, 'max': 1.0, 'label': 'Room Size'},
                'damping': {'value': 0.5, 'min': 0.0, 'max': 1.0, 'label': 'Damping'},
                'mix': {'value': 0.3, 'min': 0.0, 'max': 1.0, 'label': 'Mix'}
            },
            'ir': {
                'volume': {'value': 1.0, 'min': 0.0, 'max': 2.0, 'label': 'Volume'}
            }
        }

    def get_effect_parameters(self, effect_name):
        """Get the parameters for a specific effect."""
        return self.effect_params.get(effect_name, {})

    def update_effect_parameter(self, effect_name, param_name, value):
        """Update a parameter value for a specific effect."""
        if effect_name not in self.effect_params:
            return
        
        if param_name not in self.effect_params[effect_name]:
            return
        
        # Update the parameter value
        self.effect_params[effect_name][param_name]['value'] = value
        
        # Update the effect instance
        if effect_name == 'chorus':
            setattr(self.chorus, param_name, value)
        elif effect_name == 'drive':
            setattr(self.drive, param_name, value)
        elif effect_name == 'delay':
            setattr(self.delay, param_name, value)
        elif effect_name == 'reverb':
            setattr(self.reverb, param_name, value)

    def is_nam_file(self, file_path):
        return file_path.lower().endswith('.nam')

    def is_ir_file(self, file_path):
        return file_path.lower().endswith('.wav')

    def load_ir_file(self, file_path):
        try:
            self.ir_processor = nam_binding.IRProcessor(file_path, self.sample_rate)
            self.add_effect('IR', self.ir_processor)
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
            self.add_effect('NAM', self.nam_processor)
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

    def add_effect(self, effect_name, effect):
        """Add an effect to the signal chain."""
        self.effect_chain.append({'name': effect_name, 'effect': effect})
        print(f'Added {effect_name} to the signal chain')

    def remove_effect(self, effect_name):
        """Remove an effect from the signal chain by name."""
        self.effect_chain = [e for e in self.effect_chain if e['name'] != effect_name]
        print(f'Removed {effect_name} from the signal chain')

    def clear_effects(self):
        """Remove all effects from the signal chain."""
        self.effect_chain.clear()
        print('Cleared all effects from the signal chain')

    def process_audio(self, audio_input):
        try:
            processed_audio = audio_input.astype(np.float32)
            
            # Process through effects in specified order
            if self.effect_states['chorus']:
                processed_audio = self.chorus.process(processed_audio)
            if self.effect_states['drive']:
                processed_audio = self.drive.process(processed_audio)
            if self.effect_states['nam'] and self.nam_processor:
                processed_audio = self.nam_processor.process(processed_audio)
            if self.effect_states['ir'] and self.ir_processor:
                processed_audio = self.ir_processor.process(processed_audio)
                # Apply IR volume control
                ir_volume = self.effect_params['ir']['volume']['value']
                processed_audio = processed_audio * ir_volume
            if self.effect_states['delay']:
                processed_audio = self.delay.process(processed_audio)
            if self.effect_states['reverb']:
                processed_audio = self.reverb.process(processed_audio)
                
            return processed_audio
        except Exception as e:
            print(f'Error in audio processing: {e}')
            return audio_input

    def toggle_effect(self, effect_name):
        """Toggle the state of an effect."""
        self.effect_states[effect_name] = not self.effect_states[effect_name]
        print(f'{effect_name.capitalize()} effect: {"ON" if self.effect_states[effect_name] else "OFF"}')

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
    root.geometry('600x800')

    player = AudioPlayer()

    # Create a frame for the signal chain display
    chain_frame = tk.Frame(root, relief=tk.GROOVE, borderwidth=2)
    chain_frame.pack(pady=10, padx=10, fill=tk.X)
    
    chain_label = tk.Label(chain_frame, text="Signal Chain", justify=tk.LEFT, font=('Arial', 10, 'bold'))
    chain_label.pack(pady=5)

    # Create a frame for parameter controls
    param_frame = tk.Frame(root, relief=tk.GROOVE, borderwidth=2)
    param_frame.pack(pady=10, padx=10, fill=tk.X)
    param_label = tk.Label(param_frame, text="Effect Parameters", font=('Arial', 10, 'bold'))
    param_label.pack(pady=5)

    # Dictionary to store parameter sliders
    param_sliders = {}
    current_effect = None

    def clear_param_frame():
        for widget in param_frame.winfo_children():
            if widget != param_label:
                widget.destroy()

    def show_effect_parameters(effect_name):
        nonlocal current_effect
        current_effect = effect_name
        clear_param_frame()

        if not player.effect_states[effect_name]:
            return

        params = player.get_effect_parameters(effect_name)
        param_sliders[effect_name] = {}

        for param_name, param_info in params.items():
            # Create frame for each parameter
            slider_frame = tk.Frame(param_frame)
            slider_frame.pack(pady=5, fill=tk.X, padx=10)

            # Add label
            label = tk.Label(slider_frame, text=param_info['label'])
            label.pack(side=tk.TOP)

            # Add control (slider or button)
            if effect_name == 'delay' and param_name == 'delay_time':
                # Create tap tempo button instead of slider
                tap_button = tk.Button(
                    slider_frame,
                    text='Tap Tempo',
                    command=lambda: [
                        player.delay.tap_tempo(),
                        update_delay_time_label()
                    ]
                )
                tap_button.pack(side=tk.TOP, fill=tk.X, pady=5)
                
                # Add label to show current delay time
                time_label = tk.Label(slider_frame, text=f'Current: {param_info["value"]:.2f}s')
                time_label.pack(side=tk.TOP)
                
                def update_delay_time_label():
                    time_label.config(text=f'Current: {player.delay.delay_time:.2f}s')
                
                # Store None for delay_time slider since we're using a button
                slider = None
            else:
                # Regular parameter slider
                slider = tk.Scale(
                    slider_frame,
                    from_=param_info['min'],
                    to=param_info['max'],
                    resolution=(param_info['max'] - param_info['min']) / 100,
                    orient=tk.HORIZONTAL,
                    length=200
                )
                slider.set(param_info['value'])
                slider.pack(side=tk.TOP, fill=tk.X)

            # Store slider reference (can be None for tap tempo)
            param_sliders[effect_name][param_name] = slider

            # Add value update callback only for actual sliders
            if slider is not None:
                def make_callback(effect=effect_name, param=param_name):
                    def callback(value):
                        player.update_effect_parameter(effect, param, float(value))
                    return callback

                slider.config(command=make_callback())

    def update_chain_display():
        active_effects = [name.upper() for name, state in player.effect_states.items() if state]
        chain_text = " -> ".join(active_effects) if active_effects else "No active effects"
        chain_label.config(text=f"Signal Chain:\n{chain_text}")
        
        # Update button appearances
        for effect, button in effect_buttons.items():
            if player.effect_states[effect]:
                button.config(relief=tk.SUNKEN, bg='lightblue')
                if effect == current_effect:
                    show_effect_parameters(effect)
            else:
                button.config(relief=tk.RAISED, bg='SystemButtonFace')
                if effect == current_effect:
                    clear_param_frame()

    # Effect toggle buttons frame
    effects_frame = tk.Frame(root)
    effects_frame.pack(pady=10)

    # Create toggle buttons for each effect
    effect_buttons = {}
    for effect in ['chorus', 'drive', 'nam', 'ir', 'delay', 'reverb']:
        def make_toggle_command(effect_name):
            return lambda: [player.toggle_effect(effect_name), show_effect_parameters(effect_name), update_chain_display()]
        
        effect_buttons[effect] = tk.Button(
            effects_frame,
            text=f'{effect.upper()}',
            command=make_toggle_command(effect),
            width=10,
            relief=tk.RAISED
        )
        effect_buttons[effect].pack(pady=2)

    # File loading buttons
    load_nam_button = tk.Button(
        root,
        text='Load NAM Model',
        command=lambda: [player.load_file(), update_chain_display()]
    )
    load_nam_button.pack(pady=10)

    load_ir_button = tk.Button(
        root,
        text='Load IR File',
        command=lambda: [player.load_file(), update_chain_display()]
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