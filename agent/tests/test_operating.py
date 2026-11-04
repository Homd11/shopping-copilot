"""Real transactional operating authority; synthetic DynamoDB and no EC2/provider."""

import importlib
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from agent.admission.store import AdmissionDenied
from agent.lifecycle.store import LifecycleUnavailable
from agent.tests.test_lifecycle_dynamodb import world as _world_fixture

world = _world_fixture
INSTANCE = "i-0123456789abcdef0"


def module():
    if importlib.util.find_spec("agent.lifecycle.operating") is None:
        pytest.fail("Finite operating authority is not implemented")
    return importlib.import_module("agent.lifecycle.operating")


def initialized(world):
    op = module()
    policy = op.OperatingPolicy(str(uuid4()), "a" * 64, INSTANCE, 900, 40000)
    store = world[1]
    op.OperatingAuthority.initialize(store, policy)
    return policy, op.OperatingAuthority(store, policy)


def test_operating_authority_must_exist():
    assert module().OperatingPolicy is not None


def test_operating_100th_start_allowed_101st_refused_and_reopen_keeps_counter(world):
    policy, authority = initialized(world)
    for index in range(100):
        authority.reserve_start(f"{index:032x}")
    assert authority.status()["starts"] == 100
    other = module().OperatingAuthority(world[1], policy)
    with pytest.raises(LifecycleUnavailable):
        other.reserve_start("b" * 32)
    assert other.status()["starts"] == 100


def test_operating_duplicate_command_cannot_dispatch_again(world):
    _, authority = initialized(world)
    authority.reserve_start("a" * 32)
    with pytest.raises(LifecycleUnavailable):
        authority.reserve_start("a" * 32)
    assert authority.status()["starts"] == 1


def test_operating_last_reservation_is_atomic_across_concurrent_callers(world):
    policy, authority = initialized(world)
    for index in range(99):
        authority.reserve_start(f"{index:032x}")
    barrier = Barrier(2)

    def reserve(index):
        local = module().OperatingAuthority(world[1], policy)
        barrier.wait()
        try:
            local.reserve_start(f"{index:032x}")
            return True
        except LifecycleUnavailable:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(reserve, [100, 101])) == 1
    assert authority.status()["starts"] == 100


@pytest.mark.parametrize("damage", ["record", "marker", "hash", "closed_type"])
def test_operating_missing_or_tampered_authority_refuses_without_repair(world, damage):
    _, authority = initialized(world)
    store, client = world[1], world[-1]
    if damage == "record":
        client.delete_item(TableName=store.table, Key=store._key("operating#window"))
    else:
        key, name, value = (
            ("meta", "operating_operation", None)
            if damage == "marker"
            else ("meta", "operating_manifest", {"S": "b" * 64})
            if damage == "hash"
            else ("operating#window", "closed", {"N": "0"})
        )
        request = dict(
            TableName=store.table,
            Key=store._key(key),
            UpdateExpression="REMOVE #field" if value is None else "SET #field=:value",
            ExpressionAttributeNames={"#field": name},
        )
        if value is not None:
            request["ExpressionAttributeValues"] = {":value": value}
        client.update_item(**request)
    with pytest.raises(LifecycleUnavailable):
        authority.check()
    with pytest.raises(AdmissionDenied):
        store.check()


def test_operating_legacy_configuration_cannot_ignore_bound_marker(world):
    initialized(world)
    from agent.admission.dynamodb import DynamoInvitationStore

    store = world[1]
    with pytest.raises(AdmissionDenied):
        DynamoInvitationStore(store.client, store.table, store.namespace, store.identity)


def test_operating_marker_and_record_cannot_be_reinitialized(world):
    policy, _ = initialized(world)
    store = world[1]
    with pytest.raises(LifecycleUnavailable):
        module().OperatingAuthority.initialize(store, policy)
    store.client.delete_item(TableName=store.table, Key=store._key("operating#window"))
    with pytest.raises(LifecycleUnavailable):
        module().OperatingAuthority.initialize(store, policy)


def test_operating_expiry_close_and_observation_are_separate(world):
    _, authority = initialized(world)
    world[0][0] = 40000
    with pytest.raises(LifecycleUnavailable):
        authority.check()
    with pytest.raises(LifecycleUnavailable):
        authority.reserve_start("a" * 32)
    authority.close("expired")
    assert authority.status()["closed"] is True
    authority.check(allow_closed=True)
    with pytest.raises(AdmissionDenied):
        world[1].check()


def test_operating_clock_regression_refuses_even_within_open_window(world):
    _, authority = initialized(world)
    world[0][0] = 1200
    authority.check()
    world[0][0] = 1100
    with pytest.raises(LifecycleUnavailable):
        authority.check()


def test_operating_transaction_failure_cannot_be_retried_as_success(world, monkeypatch):
    _, authority = initialized(world)

    def fail(**kwargs):
        raise OSError("lost transactional response")

    monkeypatch.setattr(world[-1], "transact_write_items", fail)
    with pytest.raises(LifecycleUnavailable):
        authority.reserve_start("a" * 32)


@pytest.mark.parametrize(
    "field,value",
    [("instance", "i-other"), ("opens", True), ("closes", 900 + 33 * 86400)],
)
def test_operating_policy_rejects_unbounded_or_wrong_identity(world, field, value):
    op = module()
    fields = dict(
        operation=str(uuid4()), manifest_sha256="a" * 64, instance=INSTANCE, opens=900, closes=40000
    )
    fields[field] = value
    with pytest.raises(ValueError):
        op.OperatingPolicy(**fields)
