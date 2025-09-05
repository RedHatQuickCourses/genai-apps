from guardrails import Guard
from guardrails.errors import ValidationError
import warnings
import os

os.environ["GUARDRAILS_BASE_URL"] = "http://localhost:8000"

# Ignore UserWarning type warnings that pollute the console
warnings.filterwarnings("ignore", category=UserWarning)

def test_gai_server():
    print("\n=== Guardrails AI Server Testing ===")
    
    test_responses = [
        "The quick brown fox jumps over the lazy dog.",  # Valid response
        "AI and machine learning are transforming industries.",  # Another Valid response
        "flooby dooby wacka stacka gibber jabber.",  # Gibberish test
        "Damn. My bet went to hell.",  # Profanity test
        "The oracle at Delphi saw visions", # competitor check false positive
        "ibm and oracle are the top enterprise databases" # competitor check should trigger
    ]
    
    try:
        guard = Guard.fetch_guard(
            name="content_guard"
        )
        
        for i, text in enumerate(test_responses, 1):
            print(f"\nTest {i}: '{text}'")
            try:
                result = guard.validate(text)
                #print(result)
                print(f"  ✅ PASSED: {result.validation_passed}")
                if hasattr(result, 'validation_summaries'):
                    print(f"  Details: {result.validation_summaries}")
                    
            except ValidationError as ve:
                print(f"  ❌ FAILED: {ve}")
            except Exception as e:
                print(f"  ⚠️  ERROR: {e}")
                
    except Exception as e:
        print(f"Failed to connect to guard: {e}")

def main():
    # Verify if Guardrails AI server is running
    print("\nCheck if Guardrails AI server is running...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health-check")
        if response.status_code != 200:
            print("❌ Guardrails AI server is not running!")
            print("Start it with: guardrails start --config config.py")
            return
        else:
            print("✅ Guardrails AI server is running")
    except:
        print("❌ Cannot connect to Guardrails AI server!")
        print("Start it with: guardrails start --config config.py")
        return
    
    test_gai_server()

if __name__ == "__main__":
    main()
