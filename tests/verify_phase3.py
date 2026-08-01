import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_vector_db import (
    test_flatten_metadata,
    test_vector_store_ingestion_and_query
)

if __name__ == "__main__":
    print("Starting Phase 3 Vector DB Verification Tests...")
    try:
        test_flatten_metadata()
        print("✅ test_flatten_metadata passed")
        
        test_vector_store_ingestion_and_query()
        print("✅ test_vector_store_ingestion_and_query passed")
        
        print("🎉 All Phase 3 Vector DB Tests Passed Successfully!")
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
