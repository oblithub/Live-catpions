import translators as ts
import logging

class TranslationEngine:
    def __init__(self, target_language='es', service='google'):
        self.target_language = target_language
        self.service = service
        # ts.translators_pool for list of supported services
        logging.info(f"Translation engine initialized for target: {self.target_language}, service: {self.service}")

    def translate(self, text):
        if not text or not text.strip(): # Added check for empty or whitespace-only text
            logging.debug("No text provided for translation or text is empty/whitespace.")
            return None
        try:
            # Some services might require specific HTML parsing, 'html_parser' is a general good practice.
            # However, translate_text usually handles this. If issues arise, could pass html_parser='html.parser'
            translated_text = ts.translate_text(text, translator=self.service, to_language=self.target_language)
            logging.debug(f"Translated '{text[:30]}...' to '{translated_text[:30]}...'")
            return translated_text
        except Exception as e:
            logging.error(f"Error during translation using {self.service} for text '{text[:30]}...': {e}", exc_info=True)
            # Optionally try a fallback service if configured
            return f"Translation Error: {text[:20]}..." # Return part of original on error for now
