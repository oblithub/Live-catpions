# Live Caption System

This application provides real-time transcription of microphone audio and displays it as captions at the bottom of your screen.

## Prerequisites

*   Python 3.7+
*   Pip (Python package installer)

## Setup

1.  **Clone the repository (if applicable) or download the files.**
2.  **Install dependencies:**
    Open a terminal or command prompt in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Download a Vosk Language Model:**
    *   This application uses the Vosk STT engine, which requires a language model.
    *   Download a model suitable for your language from the [Vosk Model Page](https://alphacephei.com/vosk/models). (E.g., for English, `vosk-model-small-en-us-0.15` is a good starting point).
    *   Extract the model archive. You should have a folder (e.g., `vosk-model-small-en-us-0.15`).
4.  **Configure Model Path:**
    *   In `live_caption.py`, update the `MODEL_PATH` variable at the top of the script to point to the directory of your downloaded Vosk model.
        ```python
        # Path to the Vosk language model directory
        MODEL_PATH = "path/to/your/vosk-model-small-en-us-0.15"
        ```
        (Alternatively, you can place the model folder named "model" in the same directory as `live_caption.py` if you keep `MODEL_PATH = "model"`)

## Running the Application

Execute the main script:
```bash
python live_caption.py
```

## Usage

1.  **Microphone Selection:** Upon starting, a dialog will appear prompting you to enter the index of your desired microphone. A list of available microphones and their indices will be printed to the console/terminal.
2.  **Captioning:**
    *   If the microphone and STT model are initialized successfully, captioning will start automatically.
    *   Speak into your microphone, and the transcribed text will appear in the caption window.
3.  **Controls:**
    *   **Stop Button:** Click "Stop" to pause the captioning.
    *   **Start Button:** If captioning is stopped or failed to initialize, the button will show "Start". Click it to attempt to initialize and start/resume captioning.
    *   **Close Window:** Click the 'X' button on the window to stop captioning and close the application.

## Troubleshooting
*   **No input devices found / Microphone issues:** Ensure your microphone is properly connected and configured in your system. Check the console output for a list of detected devices.
*   **STT Model Not Loaded:** Verify the `MODEL_PATH` in `live_caption.py` is correct and points to a valid, extracted Vosk model directory. The application will show an error in the caption window if it fails to load the model.
*   **Low Accuracy:** Larger Vosk models generally provide better accuracy but require more resources. You can experiment with different models.
