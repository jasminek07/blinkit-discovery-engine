import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("Starting Phase 8 Chatbot Backend Verification Tests...")
try:
    from tests.test_chat import test_chat_endpoints
    test_chat_endpoints()
    print("✅ test_chat_endpoints passed")
    print("🎉 All Phase 8 Chatbot Backend Tests Passed Successfully!")
    sys.exit(0)
except Exception as e:
    import traceback
    print(f"❌ Test Failed: {e}")
    traceback.print_exc()
    sys.exit(1)
