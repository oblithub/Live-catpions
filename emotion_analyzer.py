from transformers import pipeline
import logging
import random
# import torch # Not strictly needed here if device is managed by pipeline or set to CPU

class EmotionAnalyzer:
    def __init__(self, model_name="j-hartmann/emotion-english-distilroberta-base"):
        self.model_name = model_name
        self.classifier = None
        # Common emotions from models like j-hartmann's, plus some general states
        self.mock_emotions = ["neutral", "happy", "sad", "anger", "fear", "surprise", "love", "joy", "calm", "focused", "curious"] 
        self.last_mock_emotion_index = -1 # Start at -1 so first call to cycle hits index 0
        
        logging.info(f"Attempting to load emotion classification model: {self.model_name}")
        try:
            # Forcing CPU to avoid potential issues in environments without specific GPU setup.
            # pipeline handles device selection if device is not specified,
            # but explicit CPU (-1) is safer for broader compatibility in this context.
            self.classifier = pipeline(
                "text-classification", 
                model=self.model_name, 
                tokenizer=self.model_name, 
                return_all_scores=False, # Only return the top score/label
                device=-1 # Force CPU
            )
            logging.info(f"Emotion classification model '{self.model_name}' loaded successfully on CPU.")
        except Exception as e:
            # This broad exception is to catch any Hugging Face or network error during download/load
            logging.warning(f"Failed to load emotion classification model '{self.model_name}': {e}. Emotion HUD will use mock data.", exc_info=True)
            # self.classifier remains None, which triggers mock behavior in analyze_emotion

    def analyze_emotion(self, text):
        if not text or not text.strip():
            logging.debug("No text provided for emotion analysis, returning 'neutral'.")
            return "neutral" # Default for empty text

        if self.classifier:
            try:
                results = self.classifier(text)
                # The pipeline with return_all_scores=False returns a list with a single dict: [{'label': '...', 'score': ...}]
                if results and isinstance(results, list) and len(results) > 0 and 'label' in results[0]:
                    detected_emotion = results[0]['label']
                    logging.debug(f"Analyzed emotion: '{detected_emotion}' for text: '{text[:30]}...'")
                    return detected_emotion
                else:
                    logging.warning(f"Emotion analysis returned unexpected result format: {results}")
                    return "neutral" # Fallback
            except Exception as e:
                logging.error(f"Error during emotion analysis with model: {e}", exc_info=True)
                return "neutral" # Fallback on error
        else:
            # Mock behavior: cycle through mock emotions
            self.last_mock_emotion_index = (self.last_mock_emotion_index + 1) % len(self.mock_emotions)
            mock_emotion = self.mock_emotions[self.last_mock_emotion_index]
            logging.debug(f"Using mock emotion: '{mock_emotion}' for text: '{text[:30]}...'")
            return mock_emotion

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # Test with actual model loading (might fail if offline or model is large/restricted)
    print("--- Testing with actual model (may take time or use mock if download fails) ---")
    analyzer = EmotionAnalyzer() # Uses default model
    
    test_texts = [
        "I am feeling incredibly happy today!",
        "This is really frustrating and makes me angry.",
        "I'm not sure what to think about this.",
        "Wow, that's a surprising turn of events!",
        "This is a test sentence for the emotion analyzer."
    ]
    
    for t_text in test_texts:
        emotion = analyzer.analyze_emotion(t_text)
        print(f"Text: '{t_text}' -> Detected Emotion: '{emotion}' (Classifier: {'Active' if analyzer.classifier else 'Mock'})")

    print("\n--- Testing with explicit mock behavior (simulating model load failure) ---")
    # To force mock behavior for testing, we can temporarily set classifier to None
    analyzer_mock = EmotionAnalyzer(model_name="nonexistent/model-should-fail") # This should fail and use mock
    if analyzer_mock.classifier is None: # Ensure it failed as expected
        print("Model loading failed as expected, using mock emotions for next tests.")
        for i in range(len(analyzer_mock.mock_emotions) + 2): # Cycle through all mock emotions + a couple more
             emotion = analyzer_mock.analyze_emotion(f"Mock test sentence {i+1}")
             print(f"Mock Test {i+1} -> Detected Emotion: '{emotion}'")
    else:
        print("Mock test setup failed - model that should not exist was somehow loaded.")

    print("\n--- Testing with empty/whitespace text ---")
    emotion_empty = analyzer.analyze_emotion("")
    print(f"Text: '' -> Detected Emotion: '{emotion_empty}'")
    emotion_space = analyzer.analyze_emotion("   ")
    print(f"Text: '   ' -> Detected Emotion: '{emotion_space}'")
