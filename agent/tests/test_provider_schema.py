import copy
import json

import pytest

from agent.catalogue_retrieval import DECISION
from agent.llm.config import LLMConfigurationError
from agent.llm.provider_schema import inline_schema_references, openrouter_response_schema


def test_catalogue_schema_expands_nested_references_without_losing_constraints():
    original = DECISION.json_schema()
    before = copy.deepcopy(original)
    result = inline_schema_references(original)
    assert original == before
    assert all(key not in json.dumps(result) for key in ['"$ref"', '"$defs"', '"discriminator"'])
    search = result["oneOf"][0]
    assert search["properties"]["kind"]["const"] == "search"
    assert search["additionalProperties"] is False
    query = search["properties"]["query"]
    assert query["properties"]["requirements"]["maxItems"] == 20
    money = query["properties"]["requirements"]["items"]["oneOf"][0]
    assert money["properties"]["amount"]["pattern"] == r"^(?:0|[1-9]\d*)(?:\.\d{1,2})?$"
    assert money["required"] == ["field", "op", "amount", "currency"]


@pytest.mark.parametrize("ref", ["#/$defs/missing", "#/$defs/cycle", "https://example.test/schema"])
def test_unresolvable_or_cyclic_schemas_fail_locally(ref):
    with pytest.raises(LLMConfigurationError):
        inline_schema_references({"$defs": {"cycle": {"$ref": ref}}, "$ref": ref})


def test_reference_sibling_constraints_are_intersected_instead_of_overwriting():
    result = inline_schema_references(
        {
            "$defs": {"limit": {"type": "integer", "maximum": 10}},
            "$ref": "#/$defs/limit",
            "minimum": 2,
        }
    )
    assert result == {"allOf": [{"type": "integer", "maximum": 10}, {"minimum": 2}]}


def test_provider_structural_schema_keeps_types_while_local_validator_enforces_bounds():
    schema = openrouter_response_schema(DECISION.json_schema())
    query = schema["oneOf"][0]["properties"]["query"]
    assert query["properties"]["query"]["type"] == "string"
    assert "maxLength" not in query["properties"]["query"]
    assert "maxItems" not in query["properties"]["requirements"]
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DECISION.validate_json(json.dumps({"kind": "search", "query": {"query": "x" * 1025}}))
