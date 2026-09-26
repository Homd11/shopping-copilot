import re
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from agent.llm.contract import LLMClient, LLMInvalidResponseError, LLMRequest
from agent.storefront import Money

Language = Literal["ar", "en"]
Dialect = Literal["egyptian_arabic", "franco_arabic", "mixed", "english", "unknown"]
IntentName = Literal[
    "find_products",
    "locate",
    "navigate",
    "open_product",
    "mutate",
    "cart_edit",
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
    "catalogue",
    "price_preference",
    "product_id",
    "cart_quantity",
]
RevisionField = Literal[
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
    "catalogue",
    "price_preference",
    "request_mode",
    "owned_items",
    "owned_item",
    "preferred_colors",
    "desired_wear_position",
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


class CatalogueRequirement(IntentModel):
    excluded: bool = False
    kind: Literal["feature", "suitable_for"]
    value: str
    source: str


class PricePreference(IntentModel):
    value: Literal["lower_price"]
    source: str


class OwnedItem(IntentModel):
    category: str
    product_type: str | None = None
    color: str | None = None
    source: str


class StructuredIntent(IntentModel):
    v: Literal[1, 2, 3, 4, 5, 6, 7, 8]
    language: Language
    dialect: Dialect
    intent: IntentName
    constraints: IntentConstraints
    missing_fields: list[ConstraintField]
    conflicting_fields: list[ConstraintField] = Field(default_factory=list)
    needs_clarification: bool
    catalogue_requirements: list[CatalogueRequirement] = Field(default_factory=list)
    price_preference: PricePreference | None = None
    owned_item: OwnedItem | None = None
    desired_wear_position: Literal["upper", "lower", "footwear"] | None = None
    request_mode: Literal["browse", "recommend", "style"] = "browse"
    owned_items: list[OwnedItem] = Field(default_factory=list, max_length=6)
    preferred_colors: list[str] = Field(default_factory=list, max_length=6)
    subjective_preferences: list[str] = Field(default_factory=list, max_length=6)
    navigation_source: str | None = None
    product_id: str | None = None
    revised_fields: list[RevisionField] = Field(default_factory=list)
    revision_source: str | None = None
    mutation_kind: Literal["clear_cart", "submit_checkout"] | None = None
    mutation_source: str | None = None
    cart_operation: Literal["add", "quantity", "remove", "undo"] | None = None
    cart_source: str | None = None
    cart_target: str | None = None
    cart_target_id: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Numeric ID of the observed enabled BUTTON for the selected cart operation. "
            "Never a product ID, link ID, or quantity textbox ID."
        ),
    )
    cart_quantity: int | float | None = Field(
        default=None,
        allow_inf_nan=False,
        description=(
            "For increase/decrease: the number of units requested to add/remove, not the "
            "resulting total. Runtime computes current quantity plus/minus this amount. "
            "For set: the requested final quantity. For add: units to put in the product form."
            " Preserve an out-of-range or fractional request rather than changing its value; "
            "runtime will ask for a whole quantity within 1..99."
        ),
    )

    cart_quantity_mode: Literal["set", "increase", "decrease"] | None = Field(
        default=None,
        description=(
            "Use increase/decrease for a requested change relative to the current cart "
            "quantity. Use set only for an explicitly requested final quantity (or add-form "
            "quantity). Interpret intent in the Shopper's language; do not compute a "
            "different amount to compensate for a wrong mode."
        ),
    )

    @field_validator("subjective_preferences", mode="before")
    @classmethod
    def optional_preferences_do_not_invalidate_the_request(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return list(
            dict.fromkeys(
                item.strip()
                for item in value
                if isinstance(item, str) and 0 < len(item.strip()) <= 120
            )
        )[:6]

    @property
    def context_items(self) -> list[OwnedItem]:
        items = list(self.owned_items)
        if self.owned_item is not None and self.owned_item not in items:
            items.append(self.owned_item)
        return items

    @model_validator(mode="after")
    def clarification_state_is_consistent(self) -> Self:
        if self.intent == "cart_edit":
            if self.v not in {5, 6, 7, 8} or not self.cart_operation:
                raise ValueError("Cart edit needs a supported operation")
            if (
                self.v >= 6
                and self.cart_operation == "quantity"
                and self.cart_quantity_mode is None
                and not self.needs_clarification
            ):
                raise ValueError("Quantity edits require an explicit mode")
            if self.cart_quantity_mode is not None and (
                self.v < 6
                or self.cart_quantity is None
                or not (
                    self.cart_operation == "quantity"
                    or (
                        self.v >= 8
                        and self.cart_operation == "add"
                        and self.cart_quantity_mode == "set"
                    )
                )
            ):
                raise ValueError("Quantity mode must match an explicit quantity operation")
            if any(
                value is not None
                for key, value in self.constraints.model_dump().items()
                if key not in {"size", "color"}
            ):
                raise ValueError("Cart edits cannot carry discovery constraints")
            if self.product_id or self.catalogue_requirements or self.context_items:
                raise ValueError("Cart edits must be isolated")
        elif any(
            value is not None
            for value in (
                self.cart_operation,
                self.cart_source,
                self.cart_target,
                self.cart_target_id,
                self.cart_quantity,
                self.cart_quantity_mode,
            )
        ):
            raise ValueError("Only cart edits carry cart parameters")
        if self.intent == "mutate":
            if (
                self.mutation_kind is None
                or self.constraints != IntentConstraints()
                or self.catalogue_requirements
                or self.product_id is not None
            ):
                raise ValueError("Mutation intent must be explicit and isolated")
        elif self.mutation_kind is not None or self.mutation_source is not None:
            raise ValueError("Only a mutation intent may carry mutation authority")
        if self.intent != "find_products":
            self.subjective_preferences = []
        discovery_fields = (
            "category",
            "query",
            "product_type",
            "min_price",
            "max_price",
            "size",
            "color",
            "availability",
            "sort",
        )
        has_discovery_constraints = any(
            getattr(self.constraints, field) is not None for field in discovery_fields
        ) or bool(
            self.catalogue_requirements
            or self.price_preference
            or self.context_items
            or self.desired_wear_position
            or self.request_mode != "browse"
            or self.preferred_colors
        )
        if (
            self.intent in {"navigate", "locate", "open_product"} and has_discovery_constraints
        ) or (self.intent == "find_products" and self.constraints.target is not None):
            raise ValueError("Structured Intent cannot mix navigation and discovery authority")
        if self.intent == "open_product" and self.constraints.target is not None:
            raise ValueError("A product target cannot be a Storefront destination")
        if self.intent != "open_product" and self.product_id is not None:
            raise ValueError("Product ID is only valid for opening a recommended product")
        minimum = self.constraints.min_price
        maximum = self.constraints.max_price
        prices_conflict = (
            minimum is not None
            and maximum is not None
            and minimum.to_money().amount > maximum.to_money().amount
        )
        if prices_conflict:
            required_fields = {"min_price", "max_price"}
            if not required_fields.issubset(self.conflicting_fields):
                raise ValueError("Conflicting prices must be reported as conflicting fields")
        return self


class StructuredIntentDraftError(ValueError):
    """The provider replied, but its draft cannot enter the trusted intent boundary."""


async def collect_structured_intent(client: LLMClient, request: LLMRequest) -> StructuredIntent:
    text_parts: list[str] = []
    try:
        async for chunk in client.complete(request):
            if chunk.tool_call is not None:
                raise StructuredIntentDraftError("Structured intent cannot contain a tool call")
            if chunk.text is not None:
                text_parts.append(chunk.text)
    except ValidationError as error:
        raise StructuredIntentDraftError(str(error)) from error
    except LLMInvalidResponseError as error:
        raise StructuredIntentDraftError(str(error)) from error
    if not text_parts:
        raise StructuredIntentDraftError("Structured intent response was empty")
    try:
        return StructuredIntent.model_validate_json("".join(text_parts))
    except ValidationError as error:
        raise StructuredIntentDraftError(str(error)) from error
