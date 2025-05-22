# Live Caption System

This application provides real-time transcription of microphone audio and displays it as captions at the bottom of your screen. It also features a "Say That Again" hotkey, periodic summarization bubbles, keyword-triggered popups, and a voice command visualizer.

The codebase is structured into the following modules:
*   `main_app.py`: Contains the main `App` class that orchestrates the application logic.
*   `audio_manager.py`: Manages audio input operations.
*   `stt_manager.py`: Manages Speech-to-Text (STT) operations.
*   `gui_manager.py`: Manages the Graphical User Interface (GUI).
*   `config_manager.py`: Manages loading and accessing settings from `config.ini`.
*   `summarizer_engine.py`: Manages text summarization using Hugging Face Transformers.

## Prerequisites

*   Python 3.7+
*   Pip (Python package installer)
*   (For Linux) `python3-tk` and `portaudio19-dev` (or similar, for Tkinter and PortAudio/Sounddevice dependencies). `sudo apt-get install python3-tk portaudio19-dev`
*   An internet connection is required for the first run to download the STT and summarization models.

## Setup

1.  **Clone the repository (if applicable) or download the files.**
2.  **Install dependencies:**
    Open a terminal or command prompt in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `sounddevice`, `numpy`, `vosk`, `customtkinter`, `pynput`, `transformers`, and `torch`.
3.  **Download a Vosk Language Model (for STT):**
    *   Download a model suitable for your language from the [Vosk Model Page](https://alphacephei.com/vosk/models). (E.g., for English, `vosk-model-small-en-us-0.15` is a good starting point).
    *   Extract the model archive. You should have a folder (e.g., `vosk-model-small-en-us-0.15`).
4.  **Configure the Application (`config.ini`):**
    *   When you first run the application (`python main_app.py`), a `config.ini` file will be automatically created in the same directory if it doesn't exist.
    *   Open `config.ini` in a text editor to customize settings.
    *   **Crucially, update `model_path` under the `[STT]` section to point to the directory of your downloaded Vosk model.**
    *   The summarization model (`summarizer_model_name` in `[Features]`) will be downloaded automatically on first use.
    *   Define your custom keywords and messages in the `[Keywords]` section.
    *   Define your voice commands and their confirmation messages in the `[VoiceCommands]` section.

## Running the Application

Execute the main application script:
```bash
python main_app.py
```
The `config.ini` file will be created with default values if it's missing.

**Note on First Run:** The first time you run the application, the summarization model will be downloaded from Hugging Face Hub. This can take several minutes. Check the console for download progress.

## Features

*   **Live Captioning:** Real-time transcription of selected microphone input.
*   **"Say That Again" Hotkey:** Press `Ctrl+Shift+R` to display a temporary window showing the last few seconds of transcribed text.
*   **Real-time Summarizer Bubble:** Periodically, a summary of recent transcriptions will appear in a temporary "bubble" window.
*   **Smart Keyword Popups:** Define keywords in `config.ini`. When a keyword is detected in the transcription, a small popup with a custom message appears briefly.
*   **Voice Command Visualizer:** Define voice commands in `config.ini`. When a command phrase is detected as the full transcription, a visual confirmation appears.

## Configuration (`config.ini`)

The `config.ini` file allows you to customize various aspects of the application:

```ini
[Audio]
# Default microphone index. Leave empty to always prompt for selection.
default_microphone_index =
samplerate = 44100
chunk_duration = 0.5

[STT]
# Path to the Vosk language model directory for Speech-to-Text.
model_path = model
# Log partial (intermediate) STT results to the console (True/False).
log_partial_results = False

[GUI]
# Initial window geometry (widthxheight+x_offset+y_offset).
window_geometry = 800x130+100+100
# Keep the caption window always on top of other windows (True/False).
always_on_top = True

# -- Summary Bubble specific GUI settings --
summary_bubble_width = 600
summary_bubble_height = 80
summary_bubble_y_offset = -90 
summary_bubble_frameless = False

# -- Keyword Popup specific GUI settings --
keyword_popup_width = 250
keyword_popup_height = 50
keyword_popup_x_offset_from_main = 530
keyword_popup_y_offset_from_main = 20
keyword_popup_frameless = True

# -- Voice Command Visualizer Popup specific GUI settings --
command_popup_width = 400
command_popup_height = 100
command_popup_frameless = True


[Features]
# -- "Say That Again" Feature --
say_that_again_buffer_seconds = 10
# Hotkey for "Say That Again" is Ctrl+Shift+R (hardcoded in main_app.py).
hotkey_info = Ctrl+Shift+R

# -- Summarization Bubble Feature --
summarization_interval_seconds = 30
min_words_for_summary = 20
summary_display_duration_ms = 7000
summarizer_model_name = Falconsai/text_summarization
summarizer_device =
summary_max_length = 30
summary_min_length = 5

# -- Keyword Popups Feature --
keyword_popup_duration_ms = 3000

# -- Voice Command Visualizer settings --
command_display_duration_ms = 2000


[Keywords]
# Format: keyword = message_to_display
# Keywords are matched case-insensitively as substrings.
help = Showing help information...
issue = Logging an issue...

[VoiceCommands]
# Format: command_phrase = confirmation_text_or_effect_description
# Command phrases are matched case-insensitively and must be the exact full transcription.
open file = Opening File...
save document = Saving Document...
close application = Closing App...
next slide = Next Slide
previous slide = Previous Slide
```

## Usage

1.  **Microphone Selection:** As per `default_microphone_index` or dialog.
2.  **Captioning:** Starts automatically.
3.  **Controls:**
    *   **Start/Stop Button:** Toggles live transcription.
    *   **"Say That Again" Hotkey:** `Ctrl+Shift+R`.
    *   **Summarizer Bubble:** Appears periodically.
    *   **Keyword Popups:** Appear when defined keywords are spoken.
    *   **Voice Command Visualizer:** Appears when recognized voice commands are spoken.
    *   **Close Window ('X'):** Exits the application.

## Troubleshooting
*   **Model Download Issues:** Ensure internet for first run (STT/Summarization models).
*   **No input devices/Microphone issues:** Check system settings, `config.ini`.
*   **STT Model Not Loaded:** Verify `model_path` in `config.ini`.
*   **Hotkey Not Working:** Check OS permissions.
*   **Performance Issues:** Adjust summarization settings or use CPU for summarizer.
*   **Keyword/Command Issues:**
    *   Verify definitions in `config.ini` under `[Keywords]` or `[VoiceCommands]`.
    *   Keywords are substring matched, commands are exact full phrase matched (both case-insensitive).
    *   Check console logs for errors.
*   **Configuration Issues:** Delete `config.ini` to regenerate defaults.
```
