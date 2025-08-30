import guardrails as gd
from guardrails import Guard
import warnings
import logging
import sys

# Ignore UserWarning type warnings that pollute the console
warnings.filterwarnings("ignore", category=UserWarning)

# Set presidio logger to ERROR level before importing anything that uses it
logging.getLogger('presidio-analyzer').setLevel(logging.ERROR)

# Import validators from hub (install them first!)
try:
    from guardrails.hub import ToxicLanguage
    TOXIC_AVAILABLE = True
except ImportError:
    print("ToxicLanguage not installed. Run: guardrails hub install hub://guardrails/toxic_language")
    TOXIC_AVAILABLE = False

try:
    from guardrails.hub import DetectPII  
    PII_AVAILABLE = True
except ImportError:
    print("DetectPII not installed. Run: guardrails hub install hub://guardrails/detect_pii")
    PII_AVAILABLE = False


# Example 1: Simple Toxic Language Detection with Fix
def toxic_content_example():
    """Simple toxic content filtering with on_fail='fix'"""
    if not TOXIC_AVAILABLE:
        print("Skipping toxic content example - validator not installed")
        return
        
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
        print(f"Cleaned text: {result.validated_output}")
        print(f"Validation passed: {result.validation_passed}")
    except Exception as e:
        print(f"Error: {e}")

# Example 2: PII Detection and Redaction  
def pii_redaction_example():
    """Simple PII redaction with on_fail='fix'"""
    if not PII_AVAILABLE:
        print("Skipping PII example - validator not installed")
        return
        
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
        print(f"Validation passed: {result.validation_passed}")
    except Exception as e:
        print(f"Error: {e}")


# Example 3: Combined Guards (if both available)
def combined_example():
    """Combined PII redaction and toxicity filtering"""
    if not (TOXIC_AVAILABLE and PII_AVAILABLE):
        print("Skipping combined example - need both validators installed")
        return
        
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
        print(f"Validation passed: {result.validation_passed}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    toxic_content_example()
    pii_redaction_example() 
    combined_example()

# Safe execution
if __name__ == "__main__":
    main()