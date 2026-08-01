import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_llm_agent import (
    test_rate_limiter,
    test_find_best_verbatim_match,
    test_validate_and_ground_quotes,
    test_calculate_theme_confidence,
    test_prepare_cluster_prompt_capping
)

if __name__ == "__main__":
    print("Starting Phase 5 LLM Agent Verification Tests...")
    try:
        test_rate_limiter()
        print("✅ test_rate_limiter passed")
        
        test_find_best_verbatim_match()
        print("✅ test_find_best_verbatim_match passed")
        
        test_validate_and_ground_quotes()
        print("✅ test_validate_and_ground_quotes passed")
        
        test_calculate_theme_confidence()
        print("✅ test_calculate_theme_confidence passed")
        
        test_prepare_cluster_prompt_capping()
        print("✅ test_prepare_cluster_prompt_capping passed")
        
        print("🎉 All Phase 5 LLM Agent Tests Passed Successfully!")
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
