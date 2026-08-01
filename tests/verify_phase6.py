import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_classification import (
    test_cohort_classification,
    test_opportunity_scorer
)

if __name__ == "__main__":
    print("Starting Phase 6 Classification Verification Tests...")
    try:
        test_cohort_classification()
        print("✅ test_cohort_classification passed")
        
        test_opportunity_scorer()
        print("✅ test_opportunity_scorer passed")
        
        print("🎉 All Phase 6 Classification Tests Passed Successfully!")
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
