import sounddevice as sd
import numpy as np

# SAMPLERATE and CHUNK_DURATION are no longer hardcoded here.
# They will be passed as arguments to functions that need them,
# sourced from the config file by the App class.

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
        if device['max_input_channels'] > 0:  # Check if it's an input device
            print(f"  {i}: {device['name']}")
            input_devices.append({'index': i, 'name': device['name']})
    return input_devices

def capture_audio_chunk(device_index, samplerate, chunk_duration, channels=1):
    """
    Captures an audio chunk from the specified input device.

    Args:
        device_index (int): The index of the audio input device to use.
        samplerate (int): The sampling rate in Hz.
        chunk_duration (float): Duration of the audio chunk to capture in seconds.
        channels (int): Number of audio channels (1 for mono).

    Returns:
        tuple (numpy.ndarray, bool, float): A tuple containing:
            - audio_data (numpy.ndarray): The captured audio data as a NumPy array of int16 samples.
                                         Returns None if an error occurred.
            - overflowed (bool): True if an input overflow occurred during capture, False otherwise.
            - rms (float): The Root Mean Square of the audio data. Returns 0.0 if no audio data.
    """
    try:
        with sd.InputStream(samplerate=samplerate, device=device_index, channels=channels, dtype='int16') as stream:
            frames_to_record = int(samplerate * chunk_duration)
            audio_data, overflowed = stream.read(frames_to_record)
            if overflowed:
                print("Warning: Input overflowed during audio capture.")
            
            if audio_data is not None and audio_data.size > 0:
                # Ensure audio_data is float32 for RMS calculation to avoid overflow with int16 squares
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
            else:
                rms = 0.0
            return audio_data, overflowed, rms
    except Exception as e:
        print(f"Error capturing audio: {e}")
        return None, False, 0.0
