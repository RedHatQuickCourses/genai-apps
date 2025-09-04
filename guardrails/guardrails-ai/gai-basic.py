import warnings
import logging

# Ignore UserWarning type warnings that pollute the console
warnings.filterwarnings("ignore", category=UserWarning)

# Set presidio logger to ERROR level before importing anything that uses it
logging.getLogger('presidio-analyzer').setLevel(logging.ERROR)

# Import the install class from guardrails-ai library
from guardrails import install

# Install the DetectPII validator
install(
    "hub://guardrails/detect_pii",
    install_local_models=True,
    quiet=False
)

# Import Guard and Validator
from guardrails.hub import DetectPII
from guardrails import Guard
from termcolor import colored, cprint

# Setup Guard
guard = Guard().use(
    DetectPII, ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"], "exception"
)

def valid_response():
    guard.validate("Good morning! is your email ID john dot doe at example.com?")
    print(colored('\nvalid_response(): Response from LLM is valid...', 'green'))

def invalid_response1():
    try:
        guard.validate(
        "Hi John Doe! Can you please verify your email ID john.doe@example.com"
    )
    except Exception as e: 
        msg = str(e)
        print(colored('\ninvalid_response1(): Response from LLM is invalid\n', 'red'))
        print(colored(f"{msg}", 'red', attrs=['bold']))


def invalid_response2():
    try:
        guard.validate(
        "Hi John Doe! Can you please verify your if your social security number is 615-49-2540"
    )
    except Exception as e:
        msg = str(e)
        print(colored('\ninvalid_response2(): Response from LLM is invalid\n', 'red'))
        cprint(f"{msg}", 'red', attrs=['bold'])

def invalid_response3():
    try:
        guard.validate(
        "You can contact John Doe at +1 408-447-4433"
    )
    except Exception as e:
        msg = str(e)
        print(colored('\ninvalid_response3(): Response from LLM is invalid\n', 'red'))
        cprint(f"{msg}", 'red', attrs=['bold'])


if __name__ == "__main__":
    valid_response()
    #invalid_response1()
    #invalid_response2()
    #invalid_response3()

# Bonus test
# "guard.validate("My bank account number is 123456789")" -> should pass because you have configured the validator to check only for SSN, phone and email.
# To fix the above test, you need to add "US_BANK_NUMBER" to the DetectPII object argument list when creating a Guard.
