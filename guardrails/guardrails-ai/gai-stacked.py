import sys
import warnings
import logging

# Ignore UserWarning type warnings that pollute the console
warnings.filterwarnings("ignore", category=UserWarning)

# Import Guard and Validators
from guardrails import Guard, install

install(
    "hub://guardrails/gibberish_text",
    install_local_models=True,
    quiet=False
)

install(
    "hub://guardrails/profanity_free",
    install_local_models=True,
    quiet=False
)

install(
    "hub://guardrails/competitor_check",
    install_local_models=True,
    quiet=False
)

from guardrails.hub import ProfanityFree, GibberishText, CompetitorCheck
from guardrails.errors import ValidationError
from termcolor import colored

# Setup Guard
guard = Guard().use_many(
    ProfanityFree(),
    CompetitorCheck(competitors=["Microsoft", "Oracle"]),
    GibberishText(threshold=0.5, validation_method="sentence", on_fail="exception")
)

def test_valid_response():

    llm_response = """
            The capital of France is Paris.
            """

    try:
        guard.validate(
            llm_output=llm_response,
        )
        print(colored('\ntest_valid_response(): Response from LLM is valid...', 'green'))
    except ValidationError as e:
        print(e)

def test_profanity_check():

    llm_response = """
            Goddamn you! Go to Hell!
            """

    try:
        guard.validate(
            llm_output=llm_response,
        )
        
    except ValidationError as e:
        msg = str(e)
        print(colored('\ntest_profanity_check(): Response from LLM is invalid\n', 'red'))
        print(colored(f"{msg}", 'red', attrs=['bold']))

def test_competitor_check():

    llm_response = """
            MICROSOFT stock is at an all time high.
            """

    try:
        guard.validate(
            llm_output=llm_response,
        )
        
    except ValidationError as e:
        msg = str(e)
        print(colored('\ntest_competitor_check(): Response from LLM is invalid\n', 'red'))
        print(colored(f"{msg}", 'red', attrs=['bold']))

def test_gibberish_sentence():

    llm_response = """
            FLoop goop loop doop ba da bing. The previous sentence makes no sense.
            """

    try:
        guard.validate(
            llm_output=llm_response,
        )
        
    except ValidationError as e:
        msg = str(e)
        print(colored('\ntest_gibberish_sentence(): Response from LLM is invalid\n', 'red'))
        print(colored(f"{msg}", 'red', attrs=['bold']))

if __name__ == "__main__":
    test_valid_response()
    test_profanity_check()
    test_competitor_check()
    test_gibberish_sentence()
