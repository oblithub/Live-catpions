import configparser
import os

CONFIG_FILE = 'config.ini'

def load_config():
    """Creates a ConfigParser instance and reads the config file."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def get_setting(config, section, key, fallback=None):
    """
    Safely gets a setting from the config object.
    Returns fallback if section/key is not found.
    """
    try:
        return config.get(section, key)
    except (configparser.NoSectionError, configparser.NoKeyError):
        return fallback

def getint_setting(config, section, key, fallback=0):
    """Safely gets an integer setting."""
    value = get_setting(config, section, key)
    if value is None:
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback

def getfloat_setting(config, section, key, fallback=0.0):
    """Safely gets a float setting."""
    value = get_setting(config, section, key)
    if value is None:
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback

def getboolean_setting(config, section, key, fallback=False):
    """Safely gets a boolean setting."""
    value = get_setting(config, section, key)
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', 'yes', 'on', '1'):
        return True
    if value.lower() in ('false', 'no', 'off', '0'):
        return False
    return fallback

def create_default_config_if_not_exists():
    """Creates the config.ini file with default settings if it doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()

        config['Audio'] = {
            '# Default microphone index. Leave empty to always prompt.': None,
            '# Get valid indices by running the app once.': None,
            'default_microphone_index': '',
            'samplerate': '44100',
            'chunk_duration': '0.5'
        }

        config['STT'] = {
            '# Path to the Vosk language model directory': None,
            'model_path': 'model',
            '# Log STT partial results to console (True/False)': None,
            'log_partial_results': 'False'
        }

        config['GUI'] = {
            '# Initial window geometry (widthxheight+x_offset+y_offset)': None,
            'window_geometry': '800x130+100+100', 
            '# Always on top (True/False)': None,
            'always_on_top': 'True'
        }
        
        config['Features'] = {
            '# Number of seconds of transcription to buffer for "Say That Again" feature': None,
            'say_that_again_buffer_seconds': '10',
            '# Hotkey for "Say That Again" is Ctrl+Shift+R (hardcoded for now).': None,
            '# Summarization settings': None,
            'summarization_interval_seconds': '30',
            'min_words_for_summary': '20', # Min number of words in buffer to trigger a summary
            'summary_display_duration_ms': '7000', # How long the summary bubble stays
            'summarizer_model_name': 'Falconsai/text_summarization', # Model for summarization
            '# Device for summarizer, e.g., "cpu", "cuda:0", or leave empty for auto-detect by Transformers.': None,
            'summarizer_device': '', 
            'summary_max_length': '30', # Max length of the summary in tokens
            'summary_min_length': '5'   # Min length of the summary in tokens
        }

        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"Default configuration file created at {CONFIG_FILE}")

if __name__ == '__main__':
    # Test functions
    create_default_config_if_not_exists()
    config = load_config()
    
    print(f"Model Path: {get_setting(config, 'STT', 'model_path', fallback='default_model_path')}")
    print(f"Samplerate: {getint_setting(config, 'Audio', 'samplerate', fallback=0)}")
    print(f"Log Partials: {getboolean_setting(config, 'STT', 'log_partial_results', fallback=True)}")
    print(f"Non-existent: {get_setting(config, 'STT', 'non_existent_key', fallback='Not Found')}")
    # To make comments appear correctly (without key=None), need to adjust how they're added.
    # ConfigParser by default doesn't write lines that aren't key-value pairs unless they are section comments.
    # For inline comments, they are typically stripped or need to be part of the value or key.
    # The above format will write '# comment = None' if 'None' is the value.
    # If you want comments on their own lines, you have to manually write them or use a different approach.
    # The provided default config text implies comments should be on their own lines.
    # Let's refine create_default_config_if_not_exists to write comments more cleanly.
    
    # Re-attempting create_default_config with better comment handling
    if os.path.exists(CONFIG_FILE): # Delete for fresh creation in this test
        os.remove(CONFIG_FILE)

    if not os.path.exists(CONFIG_FILE):
        default_content = """; Default configuration file for Live Caption System

[Audio]
# Default microphone index. Leave empty to always prompt.
# Get valid indices by running the app once.
default_microphone_index =
samplerate = 44100
chunk_duration = 0.5

[STT]
# Path to the Vosk language model directory
model_path = model
# Log STT partial results to console (True/False)
log_partial_results = False

[GUI]
# Initial window geometry (widthxheight+x_offset+y_offset)
window_geometry = 800x130+100+100
# Always on top (True/False)
always_on_top = True

[Features]
# Number of seconds of transcription to buffer for "Say That Again" feature
say_that_again_buffer_seconds = 10
# Hotkey for "Say That Again" is Ctrl+Shift+R (hardcoded for now).
# This comment is just for information; the hotkey itself is defined in main_app.py.
hotkey_info = Ctrl+Shift+R

# Summarization settings
summarization_interval_seconds = 30
min_words_for_summary = 20
summary_display_duration_ms = 7000
summarizer_model_name = Falconsai/text_summarization
# Device for summarizer, e.g., "cpu", "cuda:0", or leave empty for auto-detect by Transformers.
summarizer_device =
summary_max_length = 30
summary_min_length = 5

[GUI]
# ... (GUI settings continue, ensure summary bubble settings are also here or added)
# Add summary bubble specific GUI settings if not already present
# summary_bubble_width = 600 (already handled in GUIManager if needed)
# summary_bubble_height = 80
# summary_bubble_y_offset = -90
# summary_bubble_frameless = False
"""
        # Add GUI settings for summary bubble if they are meant to be configurable here
        # For now, assuming they are derived or hardcoded in GUIManager as per previous steps
        # Or add them explicitly:
        default_gui_settings_for_summary = """
summary_bubble_width = 600
summary_bubble_height = 80
summary_bubble_y_offset = -90
summary_bubble_frameless = False
"""
        # Append to GUI section or ensure these are part of the main default_content string
        # For this operation, I'll ensure the main default_content string is complete.
        # Rebuilding default_content string to include all GUI and Features settings accurately.

    if not os.path.exists(CONFIG_FILE):
        default_content = """; Default configuration file for Live Caption System

[Audio]
# Default microphone index. Leave empty to always prompt.
# Get valid indices by running the app once.
default_microphone_index =
samplerate = 44100
chunk_duration = 0.5

[STT]
# Path to the Vosk language model directory
model_path = model
# Log STT partial results to console (True/False)
log_partial_results = False

[GUI]
# Initial window geometry (widthxheight+x_offset+y_offset)
window_geometry = 800x130+100+100
# Always on top (True/False)
always_on_top = True
# Summary Bubble specific GUI settings
summary_bubble_width = 600
summary_bubble_height = 80
summary_bubble_y_offset = -90 
summary_bubble_frameless = False

[Features]
# Number of seconds of transcription to buffer for "Say That Again" feature
say_that_again_buffer_seconds = 10
# Hotkey for "Say That Again" is Ctrl+Shift+R (hardcoded for now).
hotkey_info = Ctrl+Shift+R

# Summarization settings
summarization_interval_seconds = 30
min_words_for_summary = 20
summary_display_duration_ms = 7000
summarizer_model_name = Falconsai/text_summarization
# Device for summarizer, e.g., "cpu", "cuda:0", or leave empty for auto-detect by Transformers.
summarizer_device =
summary_max_length = 30
summary_min_length = 5
"""
        with open(CONFIG_FILE, 'w') as f:
            f.write(default_content)
        print(f"Default configuration file created at {CONFIG_FILE} (with improved comments)")

    config = load_config()
    print(f"Model Path (after recreate): {get_setting(config, 'STT', 'model_path', fallback='default_model_path')}")
    print(f"Samplerate (after recreate): {getint_setting(config, 'Audio', 'samplerate', fallback=0)}")
    print(f"Log Partials (after recreate): {getboolean_setting(config, 'STT', 'log_partial_results', fallback=True)}")
    print(f"Window Geometry (after recreate): {get_setting(config, 'GUI', 'window_geometry')}")
    print(f"Default Mic Index (after recreate): '{get_setting(config, 'Audio', 'default_microphone_index')}'") # Check empty value
    print(f"Default Mic Index (fallback test): '{get_setting(config, 'Audio', 'default_microphone_index', fallback='-1')}'")
    print(f"Default Mic Index (int fallback test): {getint_setting(config, 'Audio', 'default_microphone_index', fallback=-1)}") # Test empty string to int

    # Test boolean conversion more thoroughly
    config.set('GUI', 'test_bool_true', 'TRUE')
    config.set('GUI', 'test_bool_yes', 'yes')
    config.set('GUI', 'test_bool_on', 'on')
    config.set('GUI', 'test_bool_1', '1')
    config.set('GUI', 'test_bool_false', 'FALSE')
    config.set('GUI', 'test_bool_no', 'no')
    config.set('GUI', 'test_bool_off', 'off')
    config.set('GUI', 'test_bool_0', '0')
    config.set('GUI', 'test_bool_invalid', 'maybe')

    print(f"test_bool_true: {getboolean_setting(config, 'GUI', 'test_bool_true')}")
    print(f"test_bool_yes: {getboolean_setting(config, 'GUI', 'test_bool_yes')}")
    print(f"test_bool_on: {getboolean_setting(config, 'GUI', 'test_bool_on')}")
    print(f"test_bool_1: {getboolean_setting(config, 'GUI', 'test_bool_1')}")
    print(f"test_bool_false: {getboolean_setting(config, 'GUI', 'test_bool_false')}")
    print(f"test_bool_no: {getboolean_setting(config, 'GUI', 'test_bool_no')}")
    print(f"test_bool_off: {getboolean_setting(config, 'GUI', 'test_bool_off')}")
    print(f"test_bool_0: {getboolean_setting(config, 'GUI', 'test_bool_0')}")
    print(f"test_bool_invalid (fallback to False): {getboolean_setting(config, 'GUI', 'test_bool_invalid')}")
    print(f"test_bool_invalid (fallback to True): {getboolean_setting(config, 'GUI', 'test_bool_invalid', fallback=True)}")
    print(f"test_bool_missing (fallback to False): {getboolean_setting(config, 'GUI', 'test_bool_missing')}")
    print(f"test_bool_missing (fallback to True): {getboolean_setting(config, 'GUI', 'test_bool_missing', fallback=True)}")

    # Test int conversion for empty string
    print(f"default_mic_index as int (empty string): {getint_setting(config, 'Audio', 'default_microphone_index', fallback=-1)}")
    config.set('Audio', 'test_int_valid', '123')
    config.set('Audio', 'test_int_invalid', 'abc')
    print(f"test_int_valid: {getint_setting(config, 'Audio', 'test_int_valid', fallback=-1)}")
    print(f"test_int_invalid: {getint_setting(config, 'Audio', 'test_int_invalid', fallback=-1)}")
    print(f"test_int_missing: {getint_setting(config, 'Audio', 'test_int_missing', fallback=-1)}")


    # Test float conversion
    config.set('Audio', 'test_float_valid', '123.45')
    config.set('Audio', 'test_float_invalid', 'abc.def')
    print(f"test_float_valid: {getfloat_setting(config, 'Audio', 'test_float_valid', fallback=-1.0)}")
    print(f"test_float_invalid: {getfloat_setting(config, 'Audio', 'test_float_invalid', fallback=-1.0)}")
    print(f"test_float_missing: {getfloat_setting(config, 'Audio', 'test_float_missing', fallback=-1.0)}")
