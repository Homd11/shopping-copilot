import re
from dataclasses import dataclass
from typing import Literal

from agent.schemas import Action, NavigateAction, Snapshot

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_LATIN_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
Language = Literal["ar", "en"]


def detect_language(message: str) -> Language:
    return "ar" if re.search(r"[\u0600-\u06ff]", message) else "en"


class UnsupportedShoppingTask(ValueError):
    pass


@dataclass(frozen=True)
class ActionIdentity:
    task_id: str
    action_id: str
    sequence_number: int


class ScriptedPlanner:
    def plan(self, message: str, snapshot: Snapshot, identity: ActionIdentity) -> Action:
        normalized = message.translate(_ARABIC_DIGITS).lower()
        is_arabic = detect_language(message) == "ar"
        has_shoes = is_arabic or "shoe" in normalized
        has_running = any(term in normalized for term in ("جري", "للجري", "running"))
        amount_match = re.search(r"\d+", normalized)
        if not has_shoes or not has_running or amount_match is None:
            raise UnsupportedShoppingTask(
                "The scripted planner supports the filter tracer bullet only"
            )

        maximum = int(amount_match.group())
        if is_arabic:
            arabic_maximum = str(maximum).translate(_LATIN_DIGITS)
            narration = f"هفلتر لك أحذية الجري بحد أقصى {arabic_maximum} جنيه."
        else:
            narration = f"I'll filter running shoes to a maximum of EGP {maximum}."
        return NavigateAction(
            v=1,
            type="navigate",
            task_id=identity.task_id,
            action_id=identity.action_id,
            sequence_number=identity.sequence_number,
            narration=narration,
            url=f"/c/shoes?type=running&max_price={maximum}",
        )
