from vosk import Model, KaldiRecognizer
import json

# MODEL_PATH is no longer hardcoded here.
# It will be passed as an argument to initialize_stt,
# sourced from the config file by the App class.

def initialize_stt(model_path, samplerate): 
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
        model = Model(model_path)
        recognizer = KaldiRecognizer(model, samplerate)
        print(f"Vosk STT engine initialized successfully with model: {model_path}")
        return recognizer
    except Exception as e:
        print(f"Error initializing Vosk STT with model path '{model_path}': {e}.")
        print(f"Please ensure the Vosk model is downloaded and the path is correct in your config file.")
        print("Download models from: https://alphacephei.com/vosk/models")
        return None

def transcribe_audio_chunk_vosk(recognizer, audio_chunk, log_partial_results=False):
    """
    Transcribes a chunk of audio data using the initialized Vosk recognizer.

    Args:
        recognizer (vosk.KaldiRecognizer): The active Vosk recognizer instance.
        audio_chunk (numpy.ndarray): The audio data (as int16 NumPy array) to transcribe.
        log_partial_results (bool): If True, prints partial results to the console.


    Returns:
        str: The recognized text (can be partial or final result).
             Returns an empty string if no audio data or an error occurs.
    """
    if audio_chunk is None or audio_chunk.size == 0: 
        return ""
    
    audio_chunk_bytes = audio_chunk.tobytes()

    if recognizer.AcceptWaveform(audio_chunk_bytes):
        result = json.loads(recognizer.Result())
        final_text = result.get('text', "")
        if final_text and log_partial_results: # Log final if logging partials and it's not empty
             print(f"Final STT result: \"{final_text}\"")
        return final_text
    else:
        partial_result = json.loads(recognizer.PartialResult())
        partial_text = partial_result.get('partial', "")
        if partial_text and log_partial_results:
            print(f"Partial STT result: \"{partial_text}\"")
        return partial_text
