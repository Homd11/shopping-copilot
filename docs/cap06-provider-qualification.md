# Explicit captured provider qualification

24October2026. Implementation/testing only; actual key custody, host acceptance
and deployment are not approved or established by this document.

The owner approved binding the retained OpenRouter model acceptance to the
executing release/configuration and protected custody. The owner's simplifying
amendment is authoritative: read and hash protected evidence once at startup,
with no runtime file-reading worker or per-request disk hashing. The20source
hashes remain an [offline audit](cap06-openrouter-reconciliation.md) concern.
A reviewed source bugfix follows normal release verification and explicit
rebinding; it does not require editing a runtime source-pin table.

## Explicit startup

HostSettings v1/v2 stay unchanged. With neither new option, the Agent retains its
default provider=false path. Supplying exactly one option is an error. An explicit
OpenRouter v2 startup may supply both:

```text
python -m deploy.host_agent --config ABSOLUTE_HOST_CONFIG --qualification ABSOLUTE_BINDING --qualification-sha256 OPERATOR_PINNED_SHA256
```

The operator pin is an independent trusted choice installed later in root-owned
service configuration; no evidence file approves itself. This slice does not
install those arguments or create an actual production binding. There is no
environment selector, discovery of local reports or ready=true switch.

The binding is strict version1 JSON with11exact fields, at most16384bytes. It
pins the executing release fingerprint, canonical effective provider/inference
configuration, known accepted report/reconciliation digests, private provider-key
digest, existing ledger UUID and an integer UTC validity interval of at most60days.
The model is fixed to openrouter/google/gemini-3.5-flash-lite, minimal/excluded
reasoning, existing request/output bounds and the non-resettingUSD2key cap.
The effective timeout is30seconds; the host's20second hint is not hashed as the
effective provider setting.

Beside the binding, fixed filenames accepted-report.json and reconciliation.json
must contain the original byte-identical evidence. All three, the host config and
the existing key inputs use the protected POSIX reader: absolute files outside
the release, private owner permissions, protected parents, no symlink/hardlink or
state/key aliases, with bounded stable reads. Startup also performs normal complete
release verification. The private key digest never belongs in public evidence,
repr, logs or errors. candidate_binding returns candidate bytes only; it writes,
approves, enables, settles and resets nothing.

Structural/evidence/configuration refusal occurs before SDK construction. Once
the app's single real GuardedClient/OpenRouterClient exists, validate its actual
settings, key, price limits, ledger identity/path/pages, receipt and static queue
configuration before serving. A late mismatch cleans all owned resources.

## Captured runtime behavior

The verifier retains an immutable startup snapshot and actual object references.
Runtime observations use current time, closure and in-memory bindings only.
Queue occupancy and call telemetry may change normally; they are not treated as
configuration drift. There is no qualification executor, file watch or re-hash.

Operator changes on disk become effective at restart. Deleting an evidence file
does not silently reconfigure a running Agent. Expiry, process closure, lifecycle
revocation and in-memory client/ledger/configuration drift still refuse at runtime.
Work rechecks its captured proof after lifecycle awaits; the existing final
authorization before provider POST and before exposing buffered output remain.
Stop and pending-work renewal remain independent. Closure drains the existing
provider callback and closes the lightweight verifier exactly once.

The ordinary per-POST OpenRouter key-limit/remaining-credit check and durable
allowance guard are unchanged. This verifier does not contact the provider or
assert availability, add allowance, reset theUSD2cap, settle unknown costs or
permit another qualification set. Existing uncertain reservations stay held.

## Verification frontier

Focused unit/integration checks cover strict startup inputs, zero runtime evidence
I/O, restart-only file changes, expiry across lifecycle/key/output waits, client
and custody mismatches, normal occupancy, cleanup and default-closed startup.
The new native fixture exercises original accepted evidence with synthetic key/
allowance/authority. Its actual run and immutable release/profile/result digests
will be recorded in the final evidence receipt; until then native qualification
proof is pending. Earlier native archives remain historical, unchanged evidence.

Even a passing synthetic binding is not actual-host/key qualification. Real
protected key/remaining allowance custody, host/security/systemd/reboot/capability/
metadata/log acceptance, qualified capacity, current resource/cost/rollback and
public deployment approval plus desktop/Android acceptance remain separate gates.
