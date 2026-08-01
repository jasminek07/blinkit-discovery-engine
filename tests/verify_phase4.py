import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_clustering import (
    test_hdbscan_params,
    test_clustering_with_insufficient_data,
    test_clustering_normal_flow
)

if __name__ == "__main__":
    print("Starting Phase 4 Clustering Verification Tests...")
    try:
        test_hdbscan_params()
        print("✅ test_hdbscan_params passed")
        
        test_clustering_with_insufficient_data()
        print("✅ test_clustering_with_insufficient_data passed")
        
        test_clustering_normal_flow()
        print("✅ test_clustering_normal_flow passed")
        
        print("🎉 All Phase 4 Clustering Tests Passed Successfully!")
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
