import guardrails as gd
from guardrails import Guard
import warnings
import logging

# Ignore UserWarning type warnings that pollute the console
warnings.filterwarnings("ignore", category=UserWarning)

# Set presidio logger to ERROR level before importing anything that uses it
logging.getLogger('presidio-analyzer').setLevel(logging.ERROR)

from guardrails import Guard, install

# Install required validators
install(
    "hub://guardrails/toxic_language",
    install_local_models=True,
    quiet=False
)

install(
    "hub://guardrails/detect_pii",
    install_local_models=True,
    quiet=False
)

from guardrails.hub import ToxicLanguage
from guardrails.hub import DetectPII  

# Detect toxic content and fix it
def toxic_content_example():
        
    print("=== Toxic Content Filtering Example ===")
    
    # Create guard that detects and fixes toxic content
    guard = Guard().use(
        ToxicLanguage(threshold=0.5, on_fail="fix")
    )
    
    # Test text with potentially toxic content  
    toxic_text = "You dumbass. Why did you drop the eggs?. I hope you rot in hell."
    
    print(f"Original text: {toxic_text}")
    
    try:
        # Guard will automatically clean toxic content
        result = guard.validate(toxic_text)
        print(f"Cleaned safe text: {result.validated_output}")
    except Exception as e:
        print(f"Error: {e}")

# Detect PII in text and redact it
def pii_redaction_example():
        
    print("\n=== PII Redaction Example ===")
    
    # Create guard that detects and redacts PII
    guard = Guard().use(
        DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER"], on_fail="fix")
    )
    
    # Test text with PII
    text_with_pii = "Contact me at john.doe@email.com or call 555-123-4567"
    
    print(f"Original text: {text_with_pii}")
    
    try:
        # Guard will automatically redact PII
        result = guard.validate(text_with_pii)
        print(f"Redacted text: {result.validated_output}")
    except Exception as e:
        print(f"Error: {e}")

# Validator stacking - combining both PII and Toxic content validators and fix
def combined_example():
        
    print("\n=== Combined PII + Toxicity Example ===")
    
    # Create guard with both validators
    guard = Guard().use_many(
        DetectPII(pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER"], on_fail="fix"),
        ToxicLanguage(threshold=0.5, on_fail="fix")
    )
    
    # Test text with both issues
    problematic_text = "This company's damn customer service is bloody trash! Email complaints to bad.service@company.com or call 1-800-123-1234."
    
    print(f"Original text: {problematic_text}")
    
    try:
        # Guard will fix both issues
        result = guard.validate(problematic_text)
        print(f"Cleaned text: {result.validated_output}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    toxic_content_example()
    pii_redaction_example()
    combined_example()

# Safe execution
if __name__ == "__main__":
    main()