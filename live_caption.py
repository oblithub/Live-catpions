import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer
import json
import customtkinter as ctk
import tkinter # Keep for potential future use, though ctk handles most
import threading # Will be needed if stream is opened once

# --- Global Constants ---
SAMPLERATE = 44100 # Audio sampling rate in Hz. Standard for many microphones.
CHUNK_DURATION = 0.5 # Duration of audio chunks to process in seconds. Shorter = more responsive, longer = more context for STT.
MODEL_PATH = "model" # Placeholder for the path to the Vosk STT language model directory.
                     # User MUST update this to point to their downloaded model,
                     # e.g., "path/to/your/vosk-model-small-en-us-0.15"
                     # Or, place the model folder named "model" in the same directory as this script.

def list_microphones():
    """
    Lists available audio input devices (microphones) and their indices.
    Prints the list to the console and returns a list of dictionaries,
    each containing the 'index' and 'name' of an input device.
    """
    print("Available audio input devices:")
    devices = sd.query_devices()
    input_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0: # Check if it's an input device
            print(f"  {i}: {device['name']}")
            input_devices.append({'index': i, 'name': device['name']})
    return input_devices

def capture_audio_chunk(device_index, samplerate=SAMPLERATE, channels=1, chunk_duration=CHUNK_DURATION):
    """
    Captures an audio chunk from the specified input device.

    This function opens the audio stream, reads a chunk, and then closes the stream.
    For continuous captioning, this is done repeatedly. A more advanced implementation
    might keep the stream open.

    Args:
        device_index (int): The index of the audio input device to use.
        samplerate (int): The sampling rate in Hz.
        channels (int): Number of audio channels (1 for mono).
        chunk_duration (float): Duration of the audio chunk to capture in seconds.

    Returns:
        tuple (numpy.ndarray, bool): A tuple containing:
            - audio_data (numpy.ndarray): The captured audio data as a NumPy array of int16 samples.
                                         Returns None if an error occurred.
            - overflowed (bool): True if an input overflow occurred during capture, False otherwise.
    """
    try:
        # sd.InputStream is used to capture audio.
        # dtype='int16' is specified as Vosk expects 16-bit PCM audio.
        with sd.InputStream(samplerate=samplerate, device=device_index, channels=channels, dtype='int16') as stream:
            frames_to_record = int(samplerate * chunk_duration)
            audio_data, overflowed = stream.read(frames_to_record) # Read audio frames from the stream
            if overflowed:
                print("Warning: Input overflowed during audio capture.")
            return audio_data, overflowed
    except Exception as e:
        print(f"Error capturing audio: {e}")
        return None, False

def initialize_stt(model_path, samplerate=SAMPLERATE):
    """
    Initializes the Vosk Speech-to-Text (STT) engine.

    Args:
        model_path (str): The file path to the Vosk language model directory.
        samplerate (int): The audio sampling rate in Hz (must match the model's expected rate).

    Returns:
        vosk.KaldiRecognizer: An initialized Vosk recognizer instance if successful,
                              None otherwise. Errors are printed to the console.
    """
    try:
        # The Vosk model contains language data for STT.
        model = Model(model_path)
        # The KaldiRecognizer performs the actual speech recognition.
        recognizer = KaldiRecognizer(model, samplerate)
        print("Vosk STT engine initialized successfully.")
        return recognizer
    except Exception as e:
        print(f"Error initializing Vosk STT: {e}.")
        print(f"Please ensure the Vosk model is downloaded and the path '{model_path}' is correct.")
        print("Download models from: https://alphacephei.com/vosk/models")
        return None

def transcribe_audio_chunk_vosk(recognizer, audio_chunk):
    """
    Transcribes a chunk of audio data using the initialized Vosk recognizer.

    Args:
        recognizer (vosk.KaldiRecognizer): The active Vosk recognizer instance.
        audio_chunk (numpy.ndarray): The audio data (as int16 NumPy array) to transcribe.

    Returns:
        str: The recognized text (can be partial or final result).
             Returns an empty string if no audio data or an error occurs.
    """
    if audio_chunk is None or audio_chunk.size == 0:
        return ""
    
    # Convert the NumPy array of int16 samples to bytes, which Vosk expects.
    audio_chunk_bytes = audio_chunk.tobytes()

    # recognizer.AcceptWaveform() processes the audio data.
    # It returns True if a final result is available, False for partial.
    if recognizer.AcceptWaveform(audio_chunk_bytes):
        result = json.loads(recognizer.Result()) # Get the final recognition result.
        return result.get('text', "")
    else:
        partial_result = json.loads(recognizer.PartialResult()) # Get a partial (interim) result.
        return partial_result.get('partial', "")

class CaptionWindow(ctk.CTkFrame):
    """
    A CustomTkinter Frame that serves as the GUI window for displaying live captions.
    It includes a label for the captions and a Start/Stop button.
    """
    def __init__(self, master, app_ref):
        """
        Initializes the CaptionWindow.

        Args:
            master (ctk.CTk): The parent customtkinter window (the root window).
            app_ref (App): A reference to the main App instance to interact with it (e.g., for button actions).
        """
        super().__init__(master)
        self.app = app_ref # Store reference to the main App instance to call its methods
        self.master.title("Live Captions")
        # Set window geometry (width x height + x_offset + y_offset) and make it always on top.
        self.master.geometry("800x130+100+100") # Increased height for button
        self.master.attributes("-topmost", True)
        self.master.lift() # Ensure it's brought to the front

        # Label to display the transcribed captions. Wraplength ensures text wraps within the window width.
        self.caption_label = ctk.CTkLabel(self, text="Initializing...", font=("Arial", 20), wraplength=780)
        self.caption_label.pack(pady=10, padx=20, expand=True, fill="both")

        # Start/Stop button to control the captioning process.
        # Its text and state are managed by the App class.
        self.start_stop_button = ctk.CTkButton(self, text="Loading...", command=self.toggle_captioning)
        self.start_stop_button.pack(side=tkinter.BOTTOM, pady=10)
        
        self.pack(expand=True, fill="both") # Pack the frame itself into the master window.

    def toggle_captioning(self):
        """
        Called when the Start/Stop button is clicked.
        It delegates the action to the main App instance.
        """
        if self.app.is_captioning:
            self.app.stop_captioning()
        else:
            self.app.start_captioning()

    def update_caption(self, text):
        """
        Updates the text displayed in the caption label.

        Args:
            text (str): The new text to display. Can be None to clear or set specific messages.
        """
        if text is not None:
            self.caption_label.configure(text=text)
    
    def show_message(self, text, duration=None):
        """
        Displays a temporary message in the caption label.
        If a duration is provided, the message reverts after the specified time.

        Args:
            text (str): The message to display.
            duration (int, optional): Time in milliseconds after which to revert the message.
        """
        current_text = self.caption_label.cget("text")
        self.caption_label.configure(text=text)
        if duration:
            # Determine what text to revert to based on the current captioning state.
            revert_text = "Listening..." if self.app.is_captioning else "Captioning stopped."
            if text.startswith("Failed to initialize") or text.startswith("Microphone selection cancelled"):
                 revert_text = "Click Start to retry." # Specific guidance for setup failures.
            self.master.after(duration, lambda: self.update_caption(revert_text))

class App:
    """
    The main application class. It orchestrates audio capture, STT processing,
    and GUI updates for the live captioning system.
    """
    def __init__(self, root):
        """
        Initializes the App.

        Args:
            root (ctk.CTk): The root customtkinter window.
        """
        self.root = root
        # Register a callback for the window's close button ("WM_DELETE_WINDOW" protocol).
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.model_path = MODEL_PATH # Path to Vosk model.
        self.audio_device_index = None # Will be set after user selection.
        self.recognizer = None # Vosk recognizer instance, initialized later.
        self.stream = None # Placeholder for a persistent audio stream (future enhancement).
        
        # Flag to control the captioning loop. True when captioning, False otherwise.
        self.is_captioning = False

        # Create the caption display window.
        self.caption_window = CaptionWindow(master=self.root, app_ref=self)

        # Initial attempt to set up audio/STT and start captioning.
        # The user will be prompted for microphone selection.
        self.start_captioning()

    def setup_audio_and_stt(self):
        """
        Sets up audio input (microphone selection) and initializes the STT engine.

        Returns:
            bool: True if setup was successful, False otherwise.
        """
        self.caption_window.show_message("Listing microphones...", 2000)
        available_mics = list_microphones() # Display mics in console.
        if not available_mics:
            self.caption_window.show_message("No microphones found. Please check your audio setup. Click Start to retry.", 5000)
            return False

        mic_names_str = "\n".join([f"{mic['index']}: {mic['name']}" for mic in available_mics])
        
        # Use CTkInputDialog to get microphone index from the user.
        dialog = ctk.CTkInputDialog(text=f"Available Microphones (see console for full list):\n{mic_names_str}\n\nEnter microphone index:", title="Microphone Selection")
        mic_index_str = dialog.get_input()

        if mic_index_str is None: # User cancelled the dialog.
            self.caption_window.show_message("Microphone selection cancelled. Click Start to retry.", 5000)
            return False

        try:
            self.audio_device_index = int(mic_index_str)
            if not any(mic['index'] == self.audio_device_index for mic in available_mics):
                raise ValueError("Selected index is not in the list of available microphones.")
        except ValueError as e:
            self.caption_window.show_message(f"Invalid input: {e}. Click Start to retry.", 5000)
            print(f"Error selecting microphone: {e}")
            return False

        self.caption_window.show_message(f"Selected Mic: {self.audio_device_index}. Initializing STT...", 2000)
        
        # Initialize the Vosk STT recognizer.
        self.recognizer = initialize_stt(self.model_path, samplerate=SAMPLERATE)
        if self.recognizer is None:
            # Error message already printed by initialize_stt.
            self.caption_window.show_message("Failed to load STT model. Check console. Click Start to retry.", 5000)
            return False
        
        # If recognizer is successfully created, it means the model was loaded.
        # self.caption_window.update_caption("STT Initialized. Listening...") # Done by start_captioning
        return True

    def process_audio_chunk(self):
        """
        This is the core processing loop for continuous captioning.
        It captures an audio chunk, transcribes it, and updates the GUI.
        It then schedules itself to run again using `root.after`.
        """
        # Stop processing if captioning is turned off or components are not ready.
        if not self.is_captioning or self.audio_device_index is None or self.recognizer is None:
            return

        # Capture audio from the selected microphone.
        audio_data, overflowed = capture_audio_chunk(
            self.audio_device_index, 
            samplerate=SAMPLERATE, 
            chunk_duration=CHUNK_DURATION
        )

        if overflowed:
            # Optionally, provide feedback in GUI or log more prominently.
            print(f"Warning: Audio input overflowed.")

        if audio_data is not None:
            # Transcribe the captured audio.
            text = transcribe_audio_chunk_vosk(self.recognizer, audio_data)
            if text: # Only update GUI if new text is recognized.
                self.caption_window.update_caption(text)
        else:
            # This can happen if capture_audio_chunk returns None due to an error.
            # Could add a brief message to GUI, but might be too frequent.
            print("Failed to capture audio chunk in process_audio_chunk.")

        # Schedule the next call to this method.
        # This creates a non-blocking loop that allows the GUI to remain responsive.
        # Adjust the delay (e.g., 50ms) as needed. It should be less than CHUNK_DURATION
        # to process audio in near real-time, but not too small to overload CPU.
        self.root.after(50, self.process_audio_chunk)

    def start_captioning(self):
        """
        Starts the live captioning process.
        If STT/audio is not yet set up, it calls `setup_audio_and_stt()`.
        Manages the `is_captioning` flag and updates GUI elements (button text, caption label).
        """
        # If recognizer isn't set up, attempt to set it up first.
        if not self.recognizer: 
            self.caption_window.update_caption("Initializing audio and STT...")
            if not self.setup_audio_and_stt(): # Setup failed
                # setup_audio_and_stt already shows an error message.
                # Ensure button says "Start" and is_captioning is False.
                if hasattr(self.caption_window, 'start_stop_button'):
                    self.caption_window.start_stop_button.configure(text="Start")
                self.is_captioning = False 
                return

        print("Starting captioning loop...")
        self.is_captioning = True # Enable the processing loop.
        self.caption_window.update_caption("Listening...") # Update GUI.
        if hasattr(self.caption_window, 'start_stop_button'): 
            self.caption_window.start_stop_button.configure(text="Stop") # Change button text.
        
        self.process_audio_chunk() # Kick off the audio processing loop.

    def stop_captioning(self):
        """
        Stops the live captioning process.
        Manages the `is_captioning` flag and updates GUI elements.
        """
        print("Stopping captioning loop...")
        self.is_captioning = False # Disable the processing loop.
        # Future: If using a persistent audio stream, close it here.
        self.caption_window.update_caption("Captioning stopped.") # Update GUI.
        if hasattr(self.caption_window, 'start_stop_button'): 
             self.caption_window.start_stop_button.configure(text="Start") # Change button text.

    def on_close(self):
        """
        Handles the event when the application window is closed.
        Ensures captioning is stopped and resources are cleaned up before exiting.
        """
        print("Application closing...")
        self.stop_captioning() # Stop audio processing.
        # Future: Add any other specific cleanup for recognizer or stream if needed.
        self.root.destroy() # Close the Tkinter window and exit the application.

if __name__ == '__main__':
    # Set appearance mode for customtkinter (System, Dark, Light).
    ctk.set_appearance_mode("System") 
    # Set default color theme for customtkinter widgets.
    ctk.set_default_color_theme("blue")
    
    # Create the main application window.
    root = ctk.CTk()
    # Instantiate and run the App.
    app = App(root)
    # Start the Tkinter event loop, making the GUI interactive.
    root.mainloop()
