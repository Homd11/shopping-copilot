import re
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agent.llm.contract import LLMClient, LLMRequest
from agent.storefront import Money

Language = Literal["ar", "en"]
Dialect = Literal["egyptian_arabic", "franco_arabic", "mixed", "english", "unknown"]
IntentName = Literal[
    "find_products",
    "locate",
    "navigate",
    "help",
    "off_topic",
    "unsupported",
]
ConstraintField = Literal[
    "category",
    "query",
    "product_type",
    "min_price",
    "max_price",
    "size",
    "color",
    "availability",
    "sort",
    "target",
]


class IntentModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class IntentMoney(IntentModel):
    amount: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @field_validator("amount")
    @classmethod
    def validate_decimal_text(cls, value: str) -> str:
        if re.fullmatch(r"(?:0|[1-9]\d*)(?:\.\d{1,2})?", value) is None:
            raise ValueError(
                "Money amount must be a non-negative decimal string with at most two places"
            )
        return value

    def to_money(self) -> Money:
        """Convert validated model text into the Agent's exact Money value."""
        return Money(amount=Decimal(self.amount), currency=self.currency)


class IntentConstraints(IntentModel):
    category: str | None = None
    query: str | None = None
    product_type: str | None = None
    min_price: IntentMoney | None = None
    max_price: IntentMoney | None = None
    size: str | None = None
    color: str | None = None
    availability: Literal["available", "unavailable"] | None = None
    sort: Literal["cheapest", "newest"] | None = None
    target: Literal["cart", "orders", "checkout", "account"] | None = None


class StructuredIntent(IntentModel):
    v: Literal[1]
    language: Language
    dialect: Dialect
    intent: IntentName
    constraints: IntentConstraints
    missing_fields: list[ConstraintField]
    needs_clarification: bool
    clarification_question: str | None = None

    @model_validator(mode="after")
    def clarification_state_is_consistent(self) -> Self:
        if self.needs_clarification and not self.missing_fields:
            raise ValueError("Clarification requires at least one missing field")
        if not self.needs_clarification and self.clarification_question is not None:
            raise ValueError("A clarification question requires clarification state")
        return self


async def collect_structured_intent(client: LLMClient, request: LLMRequest) -> StructuredIntent:
    text_parts: list[str] = []
    async for chunk in client.complete(request):
        if chunk.tool_call is not None:
            raise ValueError("Structured intent cannot contain a tool call")
        if chunk.text is not None:
            text_parts.append(chunk.text)
    if not text_parts:
        raise ValueError("Structured intent response was empty")
    return StructuredIntent.model_validate_json("".join(text_parts))
