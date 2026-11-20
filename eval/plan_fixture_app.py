"""Scripted multi-step plan browser fixture ONLY. It tests execution, not language accuracy.

The scripted model answers by exact message text. Every model request is recorded (prompt
version, message, plan-step marker) and served at `/__eval/plan-requests` for the browser
cases to assert on.
"""

import json

from agent.app import create_app
from agent.catalogue_contract import SearchQuery
from agent.llm import LLMChunk, LLMSettings

ADD_THEN_CART = "ضيفلي الجزمة ديه للعربية مقاس 42 بعدها افتح العربية"
ADD_STEP = "ضيفلي الجزمة ديه للعربية مقاس 42"
CART_STEP = "افتح العربية"
ADD_THEN_PANTS = "ضيفلي ده وكمان عايز بنطلون لاخويا"
ADD_STEP_2 = "ضيفلي ده"
PANTS_STEP = "عايز بنطلون لاخويا"
ADVICE = "ده الأنسب لأخوك من الكتالوج."


def intent(name, **fields):
    return {
        "v": 10,
        "language": "ar",
        "dialect": "egyptian_arabic",
        "intent": name,
        "constraints": {},
        "missing_fields": [],
        "conflicting_fields": [],
        "needs_clarification": False,
        **fields,
    }


def add_intent(context, source, **steps):
    control = next(
        e
        for e in context["current_snapshot"]["elements"]
        if e.get("form_action") == "/cart/items" and e["role"] == "button"
    )
    return intent(
        "cart_edit",
        cart_operation="add",
        cart_target_id=control["id"],
        cart_quantity=1,
        cart_quantity_mode="set",
        cart_source=source,
        **steps,
    )


class PlanModel:
    def __init__(self):
        self.requests = []

    async def complete(self, request):
        version = request.prompt_version
        if version.startswith("intent-"):
            context = json.loads(request.system.split("\n", 1)[0].split(": ", 1)[1])
            message = request.messages[-1].content
            marker = context.get("resolved_state", {}).get("_plan_step")
        else:
            context = json.loads(request.messages[0].content)
            message = context.get("message")
            marker = context.get("plan_step")
        self.requests.append({"prompt": version, "message": message, "plan_step": marker})

        if version.startswith("advice-"):
            response = {
                "v": 1,
                "message": ADVICE,
                "product_ids": [p["id"] for p in context["products"]][:1],
            }
        elif version.startswith("catalogue-decision-"):
            if message == PANTS_STEP and not context["evidence"]:
                response = {
                    "kind": "search",
                    "query": SearchQuery(
                        query="",
                        requirements=[{"field": "feature", "op": "exclude", "value": "leather"}],
                    ).model_dump(),
                }
            elif message == PANTS_STEP:
                response = {
                    "kind": "recommend",
                    "language": "ar",
                    "selected_ids": ["shoe-09"],
                    "advice_message": ADVICE,
                }
            else:
                raise ValueError("Unknown scripted decision request")
        elif message == ADD_THEN_CART:
            response = add_intent(
                context, ADD_STEP, first_step=ADD_STEP, remaining_steps=[CART_STEP]
            )
        elif message == CART_STEP:
            response = intent("navigate", constraints={"target": "cart"})
        elif message == PANTS_STEP:
            # On a product page the entry point is the action interpreter, which hands a
            # shopping search back to the catalogue decision loop.
            response = intent("find_products")
        elif message == ADD_THEN_PANTS:
            response = add_intent(
                context, ADD_STEP_2, first_step=ADD_STEP_2, remaining_steps=[PANTS_STEP]
            )
        else:
            raise ValueError("Unknown scripted plan request")
        yield LLMChunk(text=json.dumps(response, ensure_ascii=False))


def build(retrieval):
    model = PlanModel()
    application = create_app(
        llm_settings=LLMSettings(provider="groq", model="offline-fixture"),
        llm_client=model,
        catalogue_retrieval_enabled=retrieval,
    )

    @application.get("/__eval/plan-requests")
    def plan_requests():
        return model.requests

    return application


app = build(False)
retrieval_app = build(True)
