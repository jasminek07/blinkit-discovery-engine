import re
from typing import List, Dict, Any, Set
from langdetect import detect

# Regular expressions for PII detection
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'\b(?:\+?91[\s-]?)?[6-9]\d{9}\b')
AADHAAR_REGEX = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', re.IGNORECASE)
UPI_REGEX = re.compile(r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b')

# HTML & Markdown cleaner regex
HTML_CLEANER = re.compile(r'<[^>]*>')
URL_REGEX = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

def clean_text_formatting(text: str) -> str:
    """Removes HTML tags, URLs, and standardizes whitespace."""
    if not text:
        return ""
    # Strip HTML
    text = HTML_CLEANER.sub('', text)
    # Strip URLs
    text = URL_REGEX.sub('[URL]', text)
    # Standardize spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def scrub_pii(text: str) -> str:
    """Redacts PII (emails, phone numbers, Aadhaar, PAN, UPI) from the given text."""
    if not text:
        return ""
    text = EMAIL_REGEX.sub('[EMAIL_REDACTED]', text)
    text = PHONE_REGEX.sub('[PHONE_REDACTED]', text)
    text = AADHAAR_REGEX.sub('[AADHAAR_REDACTED]', text)
    text = PAN_REGEX.sub('[PAN_REDACTED]', text)
    text = UPI_REGEX.sub('[UPI_REDACTED]', text)
    return text

def is_english_or_hinglish(text: str) -> bool:
    """
    Validates if the text is English or Romanized Hindi (Hinglish).
    Accepts text that uses the Latin script and filters out non-Latin scripts 
    (e.g., Devanagari, Chinese characters).
    """
    if not text:
        return False
        
    # Check for Devanagari Hindi or Cyrillic or other non-Latin blocks
    # \u0900-\u097F is the Unicode block for Devanagari script.
    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
    if devanagari_count > 0:
        return False
        
    try:
        # Detect primary language
        lang = detect(text)
        # Standard english is accepted
        if lang == 'en':
            return True
        # Hinglish often gets misclassified as 'hi', 'so', 'it', 'et' due to Romanized words.
        # We ensure it only uses Latin alphabet characters.
        latin_char_count = len(re.findall(r'[a-zA-Z]', text))
        total_char_count = len(re.sub(r'\s+', '', text))
        
        # If the text is mostly Latin characters, it is accepted as English or Hinglish
        if total_char_count > 0 and (latin_char_count / total_char_count) > 0.8:
            return True
            
        return False
    except Exception:
        # Fallback: if language detection fails, check if the string contains only Latin text
        latin_char_count = len(re.findall(r'[a-zA-Z]', text))
        total_char_count = len(re.sub(r'\s+', '', text))
        if total_char_count > 0 and (latin_char_count / total_char_count) > 0.8:
            return True
        return False

def clean_and_normalize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes, cleans, deduplicates, and filters a list of feedback records.
    
    Args:
        records: List of raw feedback records from scrapers.
        
    Returns:
        List of cleaned, deduplicated, and validated records.
    """
    cleaned_records = []
    seen_hashes: Set[str] = set()
    
    for rec in records:
        raw_text = rec.get("raw_text", "")
        
        # 1. Clean format (HTML/URLs)
        formatted_text = clean_text_formatting(raw_text)
        
        # 2. Filter short comments (less than 5 words)
        word_count = len(formatted_text.split())
        if word_count < 5:
            continue
            
        # 3. Language Filter (English & Hinglish Latin text only)
        if not is_english_or_hinglish(formatted_text):
            continue
            
        # 4. Deduplication
        text_hash = hashlib_text(formatted_text)
        if text_hash in seen_hashes:
            continue
        seen_hashes.add(text_hash)
        
        # 5. PII Scrubbing
        sanitized_text = scrub_pii(formatted_text)
        
        # Construct cleaned record
        cleaned_rec = rec.copy()
        cleaned_rec["cleaned_text"] = sanitized_text
        # Remove raw text to ensure downstream pipeline only operates on cleaned data
        if "raw_text" in cleaned_rec:
            del cleaned_rec["raw_text"]
            
        cleaned_records.append(cleaned_rec)
        
    return cleaned_records

def hashlib_text(text: str) -> str:
    """Helper to generate hash for text deduplication."""
    # Standardize string for hash matching (lowercase, no spaces)
    normalized = re.sub(r'\s+', '', text).lower()
    import hashlib
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()
