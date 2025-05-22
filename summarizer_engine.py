from transformers import pipeline
import logging

class SummarizerEngine:
    def __init__(self, model_name="Falconsai/text_summarization", device=None): # Allow device selection
        self.model_name = model_name
        self.summarizer = None
        self.device = device # Store device for pipeline
        
        # Configure logging for this module if not already configured globally
        # This is a basic example; a more robust setup might use a shared logger.
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

        try:
            # Forcing device to CPU if None is explicitly passed and CUDA isn't the default/available
            # or if a specific device like 'cpu' or 'cuda:0' is passed.
            # pipeline handles device selection automatically if device is not specified,
            # preferring GPU if available. device=-1 typically means CPU.
            # device=None usually means auto-detect.
            # Explicitly setting device can be useful for managing resources.
            pipeline_kwargs = {"model": self.model_name, "tokenizer": self.model_name}
            if self.device is not None:
                pipeline_kwargs["device"] = self.device
            
            self.summarizer = pipeline("summarization", **pipeline_kwargs)
            logging.info(f"Summarization model '{self.model_name}' loaded successfully on device '{self.summarizer.device}'.")
        except Exception as e:
            logging.error(f"Failed to load summarization model '{self.model_name}': {e}")
            # Potentially fall back to a simpler summarizer or disable the feature
            # For now, self.summarizer will remain None, and summarize() will handle it.

    def summarize(self, text, max_length=30, min_length=5):
        if not self.summarizer:
            logging.warning("Summarizer not available or failed to load. Cannot summarize.")
            return None
        if not text or not text.strip():
            logging.info("No text provided for summarization or text is empty/whitespace.")
            return None
        
        # Pre-check for very short texts that might be shorter than min_length,
        # as some models might error or perform poorly.
        # This is a simple word count; tokenizer-based length might be more accurate.
        if len(text.split()) < min_length + 2 : # Add a small margin
            logging.info(f"Text too short for meaningful summary (less than ~{min_length+2} words). Skipping summarization.")
            return f"Content too brief: {text}" if len(text) < max_length*2 else f"Content too brief for summary."


        try:
            logging.info(f"Summarizing text (first 50 chars): '{text[:50]}...'")
            # The pipeline returns a list of dictionaries
            summary_list = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            if summary_list and isinstance(summary_list, list) and 'summary_text' in summary_list[0]:
                logging.info(f"Summary generated: '{summary_list[0]['summary_text']}'")
                return summary_list[0]['summary_text']
            else:
                logging.error(f"Summarization did not return expected output format. Output: {summary_list}")
                return None
        except Exception as e:
            logging.error(f"Error during summarization: {e}")
            # Log the text that caused the error for debugging (first 100 chars)
            logging.debug(f"Text causing summarization error (first 100 chars): {text[:100]}")
            return None

if __name__ == '__main__':
    # Basic test
    logging.basicConfig(level=logging.INFO) # Ensure logging is active for the test
    
    # Test with default model
    engine = SummarizerEngine()
    if engine.summarizer:
        test_text_long = (
            "The James Webb Space Telescope (JWST) is a space telescope designed primarily to conduct infrared astronomy. "
            "As the largest optical telescope in space, its high resolution and sensitivity allow it to view objects too old, "
            "distant, or faint for the Hubble Space Telescope. This enables investigations across many fields of astronomy "
            "and cosmology, such as observation of the first stars and the formation of the first galaxies, and detailed "
            "atmospheric characterization of potentially habitable exoplanets."
        )
        summary = engine.summarize(test_text_long, max_length=50, min_length=10)
        print(f"Long text summary: {summary}")

        test_text_short = "This is a very short text."
        summary_short = engine.summarize(test_text_short, max_length=10, min_length=2)
        print(f"Short text summary: {summary_short}")

        test_text_empty = ""
        summary_empty = engine.summarize(test_text_empty)
        print(f"Empty text summary: {summary_empty}")
    else:
        print("Summarizer engine did not initialize correctly. Skipping tests.")

    # Test with a potentially non-existent model or if there's an issue
    # engine_fail = SummarizerEngine(model_name="this/model-does-not-exist")
    # summary_fail = engine_fail.summarize("This will not be summarized.")
    # print(f"Summary with failing model: {summary_fail}")

    # Test with CPU explicitly (useful if GPU issues or for testing specific device assignment)
    # print("\nTesting with CPU explicitly:")
    # engine_cpu = SummarizerEngine(device='cpu') # or device=-1 if using older transformers
    # if engine_cpu.summarizer:
    #     summary_cpu = engine_cpu.summarize(test_text_long, max_length=50, min_length=10)
    #     print(f"CPU Long text summary: {summary_cpu}")
    # else:
    #     print("CPU Summarizer engine did not initialize correctly.")
