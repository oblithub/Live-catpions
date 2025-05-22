import customtkinter as ctk # For .after and other root methods if not fully encapsulated
from pynput import keyboard
import collections
import threading
import time 
import logging # Added for global logging setup

# Import managers and their specific components
from gui_manager import GUIManager
import audio_manager
import stt_manager 
import config_manager 
from summarizer_engine import SummarizerEngine 
from translation_engine import TranslationEngine # Import the new TranslationEngine

# --- Global Logging Setup ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(message)s'
)

class App:
    """
    The main application class. It orchestrates audio capture, STT processing,
    and GUI updates for the live captioning system by coordinating the different managers.
    """
    def __init__(self):
        """
        Initializes the App.
        """
        logging.info("Application initializing...")
        config_manager.create_default_config_if_not_exists()
        self.config = config_manager.load_config()

        self.gui_manager = GUIManager(app_ref=self, config=self.config)
        
        self.is_captioning = False
        self.audio_device_index = None
        self.recognizer = None

        # Transcription Buffer for "Say That Again"
        self.transcription_buffer_size_seconds = config_manager.getint_setting(
            self.config, 'Features', 'say_that_again_buffer_seconds', fallback=10
        )
        chunk_dur = config_manager.getfloat_setting(self.config, 'Audio', 'chunk_duration', fallback=0.5)
        if chunk_dur <= 0: chunk_dur = 0.5 
        buffer_maxlen = max(1, int(self.transcription_buffer_size_seconds / chunk_dur))
        self.transcription_buffer = collections.deque(maxlen=buffer_maxlen)
        
        self.hotkey_listener = None
        self.setup_hotkey_listener()

        # Summarization Feature Components
        summarizer_model = config_manager.get_setting(self.config, 'Features', 'summarizer_model_name', fallback='Falconsai/text_summarization')
        summarizer_device = config_manager.get_setting(self.config, 'Features', 'summarizer_device', fallback=None) 
        logging.info(f"Initializing SummarizerEngine with model: {summarizer_model}, device: {summarizer_device}")
        self.summarizer_engine = SummarizerEngine(model_name=summarizer_model, device=summarizer_device)
        
        self.summarization_text_buffer = [] 
        self.last_summary_time = time.time()
        self.summarization_interval = config_manager.getint_setting(
            self.config, 'Features', 'summarization_interval_seconds', fallback=30
        )
        self.min_words_for_summary = config_manager.getint_setting(
            self.config, 'Features', 'min_words_for_summary', fallback=20
        )
        self.summary_display_duration_ms = config_manager.getint_setting(
            self.config, 'Features', 'summary_display_duration_ms', fallback=7000
        )
        self.summary_max_length = config_manager.getint_setting(
            self.config, 'Features', 'summary_max_length', fallback=30 
        )
        self.summary_min_length = config_manager.getint_setting(
            self.config, 'Features', 'summary_min_length', fallback=5
        )

        # Keyword Popups Feature Components
        self.keywords = config_manager.load_keywords(self.config) 
        logging.info(f"Loaded keywords: {self.keywords}")
        self.keyword_popup_duration_ms = config_manager.getint_setting(
            self.config, 'Features', 'keyword_popup_duration_ms', fallback=3000
        )

        # Voice Command Visualizer Components
        self.voice_commands = config_manager.load_voice_commands(self.config)
        logging.info(f"Loaded voice commands: {self.voice_commands}")
        self.command_display_duration_ms = config_manager.getint_setting(
            self.config, 'Features', 'command_display_duration_ms', fallback=2000
        )

        # Translation Feature Components
        self.translation_enabled = config_manager.getboolean_setting(self.config, 'Features', 'translation_enabled', fallback=False)
        target_lang = config_manager.get_setting(self.config, 'Features', 'translation_target_language', fallback='es')
        translator_service = config_manager.get_setting(self.config, 'Features', 'translation_service_engine', fallback='google')

        if self.translation_enabled:
            logging.info(f"Translation enabled. Target: {target_lang}, Service: {translator_service}")
            self.translation_engine = TranslationEngine(target_language=target_lang, service=translator_service)
        else:
            self.translation_engine = None
            logging.info("Translation feature is disabled.")


        # Mic Activity Heatmap components
        self.heatmap_data_points = config_manager.getint_setting(self.config, 'Features', 'heatmap_data_points', fallback=20)
        self.mic_activity_rms_values = collections.deque(maxlen=self.heatmap_data_points)
        self.heatmap_update_interval_ms = config_manager.getint_setting(self.config, 'Features', 'heatmap_update_interval_ms', fallback=100)
        self.heatmap_max_rms_scaling = config_manager.getfloat_setting(self.config, 'Features', 'heatmap_max_rms_scaling', fallback=0.1)
        if self.heatmap_max_rms_scaling <= 0: # Prevent division by zero or negative
            logging.warning(f"heatmap_max_rms_scaling value {self.heatmap_max_rms_scaling} is invalid, defaulting to 0.1")
            self.heatmap_max_rms_scaling = 0.1
        self.heatmap_after_id = None


        self.gui_manager.get_root().protocol("WM_DELETE_WINDOW", self.on_close)
        logging.info("Starting initial captioning setup...")
        self.start_captioning()
        # Schedule the first heatmap update
        self.heatmap_after_id = self.gui_manager.get_root().after(self.heatmap_update_interval_ms, self.update_heatmap_display)


    def setup_hotkey_listener(self):
        logging.info("Setting up hotkey listener...")
        TARGET_CHAR_KEY = keyboard.KeyCode.from_char('r') 
        TARGET_MODIFIERS = {keyboard.Key.ctrl, keyboard.Key.shift} 

        current_pressed_modifiers = set()
        char_key_pressed = False

        def on_press(key):
            nonlocal char_key_pressed 
            normalized_key = key
            if hasattr(key, 'char') and key.char:
                if key.char.lower() == 'r': 
                    normalized_key = TARGET_CHAR_KEY 
                
            if normalized_key == TARGET_CHAR_KEY:
                char_key_pressed = True
            elif key in TARGET_MODIFIERS or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r or \
                 key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    current_pressed_modifiers.add(keyboard.Key.ctrl)
                elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                    current_pressed_modifiers.add(keyboard.Key.shift)
                else: 
                    current_pressed_modifiers.add(key)

            if char_key_pressed and TARGET_MODIFIERS.issubset(current_pressed_modifiers):
                logging.info("Hotkey Ctrl+Shift+R pressed for 'Say That Again'.")
                self.gui_manager.get_root().after(0, self.show_say_that_again_buffer)
        
        def on_release(key):
            nonlocal char_key_pressed 
            normalized_key = key
            if hasattr(key, 'char') and key.char:
                if key.char.lower() == 'r':
                    normalized_key = TARGET_CHAR_KEY

            if normalized_key == TARGET_CHAR_KEY:
                char_key_pressed = False
            elif key in TARGET_MODIFIERS or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r or \
                 key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    current_pressed_modifiers.discard(keyboard.Key.ctrl)
                elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                    current_pressed_modifiers.discard(keyboard.Key.shift)
                else: 
                    current_pressed_modifiers.discard(key)
        try:
            self.hotkey_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener_thread = threading.Thread(target=self.hotkey_listener.start, daemon=True)
            listener_thread.name = "HotkeyListenerThread"
            listener_thread.start()
            logging.info("Hotkey listener started successfully.")
        except Exception as e:
            logging.error(f"Failed to start hotkey listener: {e}", exc_info=True)
            self.gui_manager.get_caption_window().show_message(f"Error: Hotkey listener failed.", 5000)


    def show_say_that_again_buffer(self):
        logging.debug("Showing 'Say That Again' buffer.")
        if not self.transcription_buffer:
            buffered_text = "Buffer is empty."
            logging.debug("Transcription buffer for 'Say That Again' is empty.")
        else:
            buffered_text = " ".join(list(self.transcription_buffer))
        
        if not buffered_text.strip():
             buffered_text = "Buffer is empty or contains only whitespace."
             logging.debug("Transcription buffer for 'Say That Again' is effectively empty (whitespace).")

        try:
            root_window = self.gui_manager.get_root()
            if not root_window.winfo_exists():
                logging.warning("Cannot show 'Say That Again' buffer, root window is destroyed.")
                return

            top = ctk.CTkToplevel(root_window)
            top.title("Say That Again")
            top.geometry("600x150+150+150") 
            top.attributes("-topmost", True)
            top.lift()
            top.focus_force()

            label = ctk.CTkLabel(top, text=buffered_text, wraplength=580, font=("Arial", 16))
            label.pack(expand=True, fill="both", padx=10, pady=10)
            
            display_duration_ms = max(3000, self.transcription_buffer_size_seconds * 1000 + 2000)
            
            def safe_destroy():
                if top and top.winfo_exists():
                    logging.debug("Destroying 'Say That Again' window.")
                    top.destroy()
            
            top.after(display_duration_ms, safe_destroy)
            logging.info("'Say That Again' buffer window displayed.")
        except Exception as e:
            logging.error(f"Error creating 'Say That Again' window: {e}", exc_info=True)


    def setup_audio_and_stt(self):
        logging.info("Setting up audio and STT...")
        caption_win = self.gui_manager.get_caption_window()
        default_idx_str = config_manager.get_setting(self.config, 'Audio', 'default_microphone_index', fallback='')
        
        if default_idx_str.strip():
            try:
                self.audio_device_index = int(default_idx_str)
                logging.info(f"Using default microphone index from config.ini: {self.audio_device_index}")
                if self.audio_device_index < 0:
                    logging.warning(f"Default microphone index '{default_idx_str}' is invalid (<0). Prompting for selection.")
                    self.audio_device_index = None
            except ValueError:
                logging.warning(f"Could not parse default_microphone_index '{default_idx_str}' from config.ini. Prompting for selection.")
                self.audio_device_index = None
        else:
            self.audio_device_index = None

        if self.audio_device_index is None:
            caption_win.show_message("Listing microphones...", 2000)
            available_mics = audio_manager.list_microphones()
            if not available_mics:
                logging.warning("No microphones found.")
                caption_win.show_message("No microphones found. Please check your audio setup. Click Start to retry.", 5000)
                return False

            mic_names_str = "\n".join([f"{mic['index']}: {mic['name']}" for mic in available_mics])
            dialog_text = (f"Available Microphones (see console for full list):\n{mic_names_str}\n\n"
                           f"Enter microphone index.\n(You can set a default in {config_manager.CONFIG_FILE})")
            mic_index_str = self.gui_manager.show_mic_selection_dialog(prompt_text=dialog_text, title="Microphone Selection")

            if mic_index_str is None:
                logging.info("Microphone selection cancelled by user.")
                caption_win.show_message("Microphone selection cancelled. Click Start to retry.", 5000)
                return False

            try:
                self.audio_device_index = int(mic_index_str)
                if not any(mic['index'] == self.audio_device_index for mic in available_mics):
                    raise ValueError("Selected index is not in the list of available microphones.")
            except ValueError as e:
                logging.error(f"Invalid microphone index input: {e}", exc_info=True)
                caption_win.show_message(f"Invalid input: {e}. Click Start to retry.", 5000)
                return False

        caption_win.show_message(f"Selected Mic: {self.audio_device_index}. Initializing STT...", 2000)
        model_path = config_manager.get_setting(self.config, 'STT', 'model_path', fallback='model')
        samplerate = config_manager.getint_setting(self.config, 'Audio', 'samplerate', fallback=44100)

        self.recognizer = stt_manager.initialize_stt(model_path, samplerate)
        if self.recognizer is None:
            logging.error(f"Failed to load STT model from '{model_path}'.")
            caption_win.show_message(f"Failed to load STT model from '{model_path}'. Check console. Click Start to retry.", 5000)
            return False
        logging.info("Audio and STT setup successful.")
        return True

    def _trigger_summarization(self, text_to_summarize):
        logging.info(f"Triggering summarization for text of length {len(text_to_summarize)} chars.")
        summary = self.summarizer_engine.summarize(
            text_to_summarize, 
            max_length=self.summary_max_length, 
            min_length=self.summary_min_length
        )
        if summary:
            logging.info(f"Summary generated: '{summary}'")
            self.gui_manager.get_root().after(
                0, 
                self.gui_manager.show_summary_bubble, 
                summary, 
                self.summary_display_duration_ms
            )
        else:
            logging.warning("Summarization returned no result or failed.")


    def process_audio_chunk(self):
        if not self.is_captioning or self.audio_device_index is None or self.recognizer is None:
            return

        samplerate = config_manager.getint_setting(self.config, 'Audio', 'samplerate', fallback=44100)
        chunk_duration = config_manager.getfloat_setting(self.config, 'Audio', 'chunk_duration', fallback=0.5)

        audio_data, overflowed, rms = audio_manager.capture_audio_chunk(
            self.audio_device_index, samplerate=samplerate, chunk_duration=chunk_duration
        )

        if overflowed: logging.warning(f"Audio input overflowed.")
        
        # Process RMS for heatmap
        if rms is not None:
            normalized_rms = min(rms / self.heatmap_max_rms_scaling, 1.0)
            self.mic_activity_rms_values.append(normalized_rms)
            # logging.debug(f"RMS: {rms}, Normalized: {normalized_rms}, Buffer: {list(self.mic_activity_rms_values)}") # Very verbose
        else:
            self.mic_activity_rms_values.append(0.0)


        caption_win = self.gui_manager.get_caption_window()
        if audio_data is not None:
            log_partial = config_manager.getboolean_setting(self.config, 'STT', 'log_partial_results', fallback=False)
            text = stt_manager.transcribe_audio_chunk_vosk(self.recognizer, audio_data, log_partial_results=log_partial)
            
            if text and text.strip(): 
                processed_text_for_features = text.strip() 
                self.transcription_buffer.append(processed_text_for_features) 
                self.summarization_text_buffer.append(processed_text_for_features) 

                # Voice Command detection 
                # Voice commands usually need to be precise and might be the whole utterance.
                lower_full_text = processed_text_for_features.lower()
                command_detected = False
                if self.voice_commands:
                    for command_phrase, confirmation_message in self.voice_commands.items():
                        # command_phrase is already lowercase from load_voice_commands
                        if command_phrase == lower_full_text:
                            logging.info(f"Voice command '{command_phrase}' detected. Displaying: '{confirmation_message}'")
                            self.gui_manager.get_root().after(
                                0,
                                self.gui_manager.show_command_visualizer,
                                confirmation_message,
                                self.command_display_duration_ms
                            )
                            command_detected = True
                            break 
                
                # Keyword detection (only if a specific voice command wasn't detected)
                if not command_detected and self.keywords:
                    # For keywords, we might want to search within the text, not exact match of whole phrase.
                    # The current keyword logic iterates and finds 'keyword in lower_text'.
                    # This means 'help me' would trigger 'help' keyword.
                    # This is fine for keywords, but commands are usually more specific.
                    lower_text_for_keywords = processed_text_for_features.lower() # Can be different from command text if needed
                    for keyword, message in self.keywords.items():
                        if keyword in lower_text_for_keywords:
                            logging.info(f"Keyword '{keyword}' detected. Displaying message: '{message}'")
                            self.gui_manager.get_root().after(
                                0, 
                                self.gui_manager.show_keyword_popup, 
                                message, 
                                self.keyword_popup_duration_ms
                            )
                            break 
                
                # Translation (after commands and keywords, on the same processed_text_for_features)
                if self.translation_engine: # Check if translation_engine is initialized
                    # Run translation in a thread
                    translation_thread = threading.Thread(
                        target=self._trigger_translation, 
                        args=(processed_text_for_features,), # Use the same stripped text
                        daemon=True
                    )
                    translation_thread.name = "TranslationThread"
                    translation_thread.start()
            
            if text: 
                caption_win.update_caption(text)
        else:
            logging.warning("Failed to capture audio chunk in process_audio_chunk.")

        current_time = time.time()
        if (current_time - self.last_summary_time) > self.summarization_interval:
            full_text_to_summarize = " ".join(self.summarization_text_buffer)
            logging.debug(f"Summarization check: Current buffer length {len(full_text_to_summarize.split())} words, min_words: {self.min_words_for_summary}")

            if len(full_text_to_summarize.split()) >= self.min_words_for_summary:
                logging.info("Sufficient text collected, starting summarization thread.")
                summary_thread = threading.Thread(
                    target=self._trigger_summarization, 
                    args=(full_text_to_summarize,), 
                    daemon=True
                )
                summary_thread.name = "SummarizerThread"
                summary_thread.start()
                self.summarization_text_buffer = [] 
            elif self.summarization_text_buffer: 
                logging.info("Not enough text for summary, clearing summarization buffer as interval passed.")
                self.summarization_text_buffer = []
            
            self.last_summary_time = current_time

        self.gui_manager.get_root().after(50, self.process_audio_chunk)

    def start_captioning(self):
        logging.info("Attempting to start captioning...")
        caption_win = self.gui_manager.get_caption_window()
        if not self.recognizer: 
            caption_win.update_caption("Initializing audio and STT...")
            if not self.setup_audio_and_stt():
                logging.warning("Captioning start failed: setup_audio_and_stt returned False.")
                if hasattr(caption_win, 'start_stop_button'):
                     caption_win.start_stop_button.configure(text="Start")
                self.is_captioning = False
                return

        logging.info("Starting captioning loop...")
        self.is_captioning = True
        caption_win.update_caption("Listening...")
        if hasattr(caption_win, 'start_stop_button'):
            caption_win.start_stop_button.configure(text="Stop")
        self.process_audio_chunk()

    def stop_captioning(self):
        logging.info("Stopping captioning loop.")
        self.is_captioning = False
        caption_win = self.gui_manager.get_caption_window()
        caption_win.update_caption("Captioning stopped.")
        if hasattr(caption_win, 'start_stop_button'):
             caption_win.start_stop_button.configure(text="Start")

    def on_close(self):
        logging.info("Application closing...")
        self.stop_captioning()
        if self.hotkey_listener:
            logging.info("Stopping hotkey listener...")
            self.hotkey_listener.stop()
        
        if self.heatmap_after_id:
            logging.info("Cancelling heatmap display updates.")
            self.gui_manager.get_root().after_cancel(self.heatmap_after_id)
            self.heatmap_after_id = None

        logging.info("Destroying GUI.")
        self.gui_manager.get_root().destroy()

    def update_heatmap_display(self):
        """Periodically updates the microphone activity heatmap display."""
        current_rms_list = list(self.mic_activity_rms_values)
        
        # Pad with zeros if not enough data points yet, ensuring it's from the left (older data)
        # The deque already handles maxlen, so we need to ensure the list passed to GUI is full length
        padded_rms_list = [0.0] * (self.heatmap_data_points - len(current_rms_list)) + current_rms_list
        
        self.gui_manager.update_mic_activity_display(padded_rms_list)
        
        # Reschedule itself
        if self.is_captioning or not all(v == 0.0 for v in padded_rms_list): # Continue if captioning or if heatmap has activity
            self.heatmap_after_id = self.gui_manager.get_root().after(self.heatmap_update_interval_ms, self.update_heatmap_display)
        else:
            logging.debug("Heatmap updates paused as captioning is off and heatmap is clear.")
            self.heatmap_after_id = None # Stop updates if not captioning and heatmap is all zeros

if __name__ == '__main__':
    app = App()
    app.gui_manager.run_mainloop()
    logging.info("Application has exited.")
