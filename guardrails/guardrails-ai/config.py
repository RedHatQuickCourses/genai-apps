from guardrails import Guard
from guardrails.hub import ProfanityFree, GibberishText, CompetitorCheck

guard = Guard()
guard.name = 'content_guard'

guard.use_many(
    ProfanityFree(),
    CompetitorCheck(competitors=["Microsoft", "Oracle"]),
    GibberishText(threshold=0.5, validation_method="sentence")
)