
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

guard = Guard()
guard.name = 'content_guard'

guard.use_many(
    ProfanityFree(),
    CompetitorCheck(competitors=["Microsoft", "Oracle"]),
    GibberishText(threshold=0.5, validation_method="sentence")
)
