import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_ingestion import (
    test_clean_text_formatting,
    test_scrub_pii,
    test_is_english_or_hinglish,
    test_clean_and_normalize_records,
    test_scrapers_initialization,
    test_pipeline_file_generation
)

if __name__ == "__main__":
    print("Starting Phase 2 Ingestion & Normalization Verification Tests...")
    try:
        test_clean_text_formatting()
        print("✅ clean_text_formatting tests passed")
        
        test_scrub_pii()
        print("✅ scrub_pii tests passed")
        
        test_is_english_or_hinglish()
        print("✅ is_english_or_hinglish tests passed")
        
        test_clean_and_normalize_records()
        print("✅ clean_and_normalize_records tests passed")
        
        test_scrapers_initialization()
        print("✅ scrapers_initialization tests passed")
        
        test_pipeline_file_generation()
        print("✅ pipeline_file_generation tests passed")
        
        print("🎉 All Phase 2 Ingestion & Normalization Tests Passed Successfully!")
        sys.exit(0)
    except AssertionError as e:
        import traceback
        print(f"❌ Test Failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"❌ Unexpected Error: {e}")
        traceback.print_exc()
        sys.exit(1)
