"""DISPOSABLE Windows browser proof; explicit temporary user-CA trust required."""

import argparse
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / ".scratch/cap04-cloud-readiness/probe"
TLS = DIR / "tls"
PANEL = "https://panel.copilot.test:4443"
STORE = "https://store.merchant.test:4443"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
PROCESSES = []
RESULT = {"paid_calls": 0, "runtime_source_changes": False, "checks": []}


def command(args, **kwargs):
    return subprocess.run(args, check=True, creationflags=FLAGS, capture_output=True, **kwargs)


def certificates():
    TLS.mkdir(exist_ok=True)
    ssl = shutil.which("openssl")
    assert ssl
    command(
        [
            ssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-noenc",
            "-days",
            "2",
            "-keyout",
            str(TLS / "ca.key"),
            "-out",
            str(TLS / "ca.pem"),
            "-subj",
            "/CN=Copilot disposable CAP04 probe",
            "-addext",
            "basicConstraints=critical,CA:TRUE,pathlen:0",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
            "-addext",
            "nameConstraints=critical,permitted;DNS:copilot.test,permitted;DNS:merchant.test",
        ]
    )
    command(
        [
            ssl,
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-noenc",
            "-keyout",
            str(TLS / "leaf.key"),
            "-out",
            str(TLS / "leaf.csr"),
            "-subj",
            "/CN=panel.copilot.test",
        ]
    )
    (TLS / "leaf.ext").write_text(
        "basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:panel.copilot.test,DNS:store.merchant.test\n"
    )
    command(
        [
            ssl,
            "x509",
            "-req",
            "-in",
            str(TLS / "leaf.csr"),
            "-CA",
            str(TLS / "ca.pem"),
            "-CAkey",
            str(TLS / "ca.key"),
            "-CAcreateserial",
            "-out",
            str(TLS / "leaf.pem"),
            "-days",
            "2",
            "-extfile",
            str(TLS / "leaf.ext"),
        ]
    )
    der = command([ssl, "x509", "-in", str(TLS / "ca.pem"), "-outform", "DER"]).stdout
    (TLS / "ca.cer").write_bytes(der)
    return hashlib.sha1(der).hexdigest()


def start(args, env, name):
    with open(DIR / f"{name}.log", "wb") as log:
        process = subprocess.Popen(
            args, cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=FLAGS
        )
    PROCESSES.append(process)


def wait_port(port):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        if any(p.poll() is not None for p in PROCESSES):
            raise RuntimeError("Probe service exited; inspect private local logs")
        time.sleep(0.1)
    raise RuntimeError(f"No listener on {port}")


def record(name, data=True):
    RESULT["checks"].append({"name": name, "result": data})
    print(name, json.dumps(data, ensure_ascii=True), flush=True)


def page_for(context):
    page = context.new_page()
    cdp = context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send(
        "Network.setCookieControls",
        {
            "enableThirdPartyCookieRestriction": True,
            "disableThirdPartyCookieMetadata": True,
            "disableThirdPartyCookieHeuristics": True,
        },
    )
    return page


def frame_for(page):
    return page.frame_locator("#storefront-frame")


def in_store(page, script, arg=None):
    return frame_for(page).locator("body").evaluate(script, arg)


def state(page):
    return in_store(
        page,
        "async () => {const r=await fetch('/cart/state');"
        " return {status:r.status,body:await r.json()};}",
    )


def navigate(page, path):
    in_store(page, "(_, path) => {location.href=path}", path)


def add(page, quantity):
    frame = frame_for(page)
    navigate(page, "/p/shoe-09")
    expect(frame.locator("#product-size")).to_be_visible()
    frame.locator("#product-size").select_option("43")
    frame.locator("#product-color").select_option("blue")
    frame.locator('input[name="quantity"]').fill(str(quantity))
    frame.locator('[data-testid="add-to-cart"]').click()
    expect(frame.locator("#cart-feedback")).to_have_text("تمت الإضافة إلى السلة")


class IsolatedBrowsers:
    """Each Shopper gets an owned profile with explicit browser privacy settings."""

    def __init__(self, playwright, channel):
        self.playwright = playwright
        self.channel = channel

    @contextmanager
    def new_context(self):
        with TemporaryDirectory(prefix="copilot-browser-proof-") as profile:
            default = Path(profile) / "Default"
            default.mkdir()
            (default / "Preferences").write_text(
                json.dumps(
                    {
                        "profile": {"cookie_controls_mode": 1, "block_third_party_cookies": True},
                        "tracking_protection": {"block_all_3pc_toggle_enabled": True},
                    }
                )
            )
            context = self.playwright.chromium.launch_persistent_context(
                profile,
                headless=True,
                channel=None if self.channel == "chromium" else self.channel,
                args=[
                    "--host-resolver-rules=MAP panel.copilot.test 127.0.0.1, "
                    "MAP store.merchant.test 127.0.0.1",
                    "--no-proxy-server",
                    "--test-third-party-cookie-phaseout",
                ],
            )
            RESULT["browser_version"] = context.browser.version
            try:
                yield context
            finally:
                context.close()


def test(browser):
    for mode in ["strict", "none", "partitioned"]:
        (DIR / "mode.txt").write_text(mode)
        with browser.new_context() as context:
            page = page_for(context)
            errors = []
            page.on("pageerror", lambda e, errors=errors: errors.append(str(e)[:160]))
            response = page.goto(PANEL)
            assert response is not None
            assert page.evaluate("window.isSecureContext")
            assert response.security_details()["protocol"] in {"TLS 1.2", "TLS 1.3"}
            expect(frame_for(page).locator("h1")).to_be_visible()
            control = in_store(
                page,
                "async () => {await fetch('/__probe/cookie-control');"
                "return (await fetch('/__probe/cookie-echo')).json()}",
            )
            assert control == {"unpartitioned": False, "partitioned": True}, control
            record(f"{mode}: third-party cookie negative control", control)
            if mode != "partitioned":
                expect(page.locator("#shopper-message")).to_be_disabled()
                assert state(page)["status"] == 401
                record(f"{mode}: linking rejected", {"cart_status": 401, "input_disabled": True})
            else:
                record(
                    "partitioned: browser storage",
                    in_store(
                        page,
                        "() => {try {sessionStorage.setItem('probe','1');"
                        "sessionStorage.removeItem('probe');return 'available'}"
                        "catch(e){return e.name+': '+e.message}}",
                    ),
                )
                record("partitioned: page errors", errors)
                record("partitioned: cart HTTP status", state(page)["status"])
                expect(page.locator("#shopper-message")).to_be_enabled(timeout=15000)
                record("partitioned: linked")
                record("page errors", errors)
                journey(browser, context, page)


def journey(browser, context, a):
    with browser.new_context() as b_context:
        b = page_for(b_context)
        streams = []
        b.on(
            "response",
            lambda r: streams.append(parse_qs(urlsplit(r.url).query).get("after", ["0"])[0])
            if "/events?" in r.url and r.status == 200
            else None,
        )
        b.goto(PANEL)
        expect(b.locator("#shopper-message")).to_be_enabled(timeout=15000)
        add(a, 1)
        add(b, 3)
        assert state(a)["body"]["lines"][0]["quantity"] == 1
        assert state(b)["body"]["lines"][0]["quantity"] == 3
        record("two-browser isolated carts")
        # Keep authoritative reads in the iframe: page.request does not model its partition.
        a.reload()
        expect(a.locator("#shopper-message")).to_be_enabled(timeout=15000)
        assert state(a)["body"]["lines"][0]["quantity"] == 1
        record("refresh retains embedded cart")
        top = page_for(context)
        top.goto(STORE)
        top_state = top.evaluate("async () => (await fetch('/cart/state')).json()")
        assert top_state["lines"] == []
        assert state(a)["body"]["lines"][0]["quantity"] == 1
        top.close()
        record("top-level Storefront has separate partition")
        tab = page_for(context)
        tab.goto(PANEL)
        expect(tab.locator("#task-status")).to_contain_text("another tab", timeout=15000)
        assert state(tab)["body"]["lines"][0]["quantity"] == 1
        tab.close()
        record("second Panel tab shares cart but cannot take task")
        # Real model-free Copilot request, bound Confirmation, reconnect and exact Undo.
        navigate(a, "/cart")
        expect(frame_for(a).locator('[data-testid="empty-cart"]')).to_be_visible()
        a.locator("#shopper-message").fill("Empty my cart")
        a.get_by_role("button", name="إرسال", exact=True).click()
        card = a.locator(".confirmation-card")
        expect(card).to_contain_text("Remove every item", timeout=15000)
        assert len(state(a)["body"]["lines"]) == 1
        record("guarded clear awaits Confirmation")
        card.get_by_role("button", name="Confirm", exact=True).click()
        expect(a.locator("#task-status")).to_have_attribute(
            "data-task-state", "completed", timeout=15000
        )
        assert state(a)["body"]["lines"] == []
        assert state(b)["body"]["lines"][0]["quantity"] == 3
        record("confirmed clear affects only owner")
        # Manual reversible Mutation proves cookie/CSRF/Undo over cross-site HTTPS.
        add(a, 2)
        frame_for(a).locator('[data-testid="undo-cart"]').click()
        expect(frame_for(a).locator("#cart-feedback")).to_contain_text("التراجع")
        assert state(a)["body"]["lines"] == []
        record("Undo restores exact cart")
        revision = state(b)["body"]["revision"]
        prior_streams = len(streams)
        assert prior_streams >= 1
        b_context.set_offline(True)
        b.wait_for_timeout(1200)
        b_context.set_offline(False)
        deadline = time.monotonic() + 20
        while len(streams) <= prior_streams and time.monotonic() < deadline:
            b.wait_for_timeout(100)
        assert len(streams) > prior_streams, "SSE did not actually reconnect"
        expect(b.locator("#shopper-message")).to_be_enabled(timeout=15000)
        assert state(b)["body"]["revision"] == revision
        record(
            "SSE connection restoration (Action replay unverified)",
            {"new_streams": len(streams) - prior_streams, "cursor": streams[-1]},
        )
        # Browser-side hostile Mutation must still fail without CSRF authority.
        denied = in_store(
            b,
            "async () => (await fetch('/cart/items',{method:'POST',"
            "headers:{'Content-Type':'application/json'},"
            "body:JSON.stringify({product_id:'shoe-09',quantity:9})})).status",
        )
        assert denied == 403
        record("missing CSRF remains rejected", denied)


def cleanup(processes, thumb, tls, report, result):
    """Attempt every cleanup independently; report any failure without hiding later work."""
    errors = []
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception as error:
                errors.append("service stop: " + type(error).__name__)
        except Exception as error:
            errors.append("service stop: " + type(error).__name__)
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception as retry_error:
                errors.append("service kill: " + type(retry_error).__name__)
    try:
        command(["certutil", "-user", "-delstore", "Root", thumb])
    except Exception as error:
        errors.append("certificate removal: " + type(error).__name__)
    result["temporary_ca_removed"] = False
    try:
        result["temporary_ca_removed"] = (
            subprocess.run(
                ["certutil", "-user", "-store", "Root", thumb],
                capture_output=True,
                creationflags=FLAGS,
            ).returncode
            != 0
        )
        if not result["temporary_ca_removed"]:
            errors.append("certificate remains; consult trust-cleanup.json")
    except Exception as error:
        errors.append("certificate verification: " + type(error).__name__)
    for name in ["ca.key", "leaf.key"]:
        try:
            (tls / name).unlink(missing_ok=True)
        except Exception as error:
            errors.append("private key removal: " + type(error).__name__)
    result["cleanup_errors"] = errors
    if errors:
        result["outcome"] = "failed"
    # Persist even when an earlier cleanup step failed. A write failure still raises.
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
    if errors:
        raise RuntimeError("Probe cleanup failed: " + "; ".join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-temporary-user-ca", action="store_true")
    parser.add_argument("--channel", choices=["chromium", "chrome", "msedge"], default="chromium")
    args = parser.parse_args()
    if os.name != "nt" or not args.allow_temporary_user_ca:
        parser.error("Windows only; requires explicit --allow-temporary-user-ca approval")
    DIR.mkdir(parents=True, exist_ok=True)
    RESULT["channel"] = args.channel
    RESULT["tls_verification"] = "default browser trust; no certificate bypass"
    RESULT["cookie_control"] = (
        "profile third-party blocking plus CDP/phaseout, verified with iframe negative control"
    )
    for port in (4000, 8000, 4443):
        with socket.socket() as s:
            assert s.connect_ex(("127.0.0.1", port)) != 0, (
                f"Port {port} is occupied; leave existing service alone"
            )
    thumb = certificates()
    RESULT["temporary_ca_thumbprint"] = thumb
    (DIR / "trust-cleanup.json").write_text(
        json.dumps({"thumbprint": thumb, "store": "CurrentUser Root"})
    )
    try:
        command(["certutil", "-user", "-addstore", "Root", str(TLS / "ca.cer")])
        env = dict(os.environ)
        env.update(
            LLM_PROVIDER="scripted",
            LLM_MODEL="scripted-v1",
            COPILOT_EVALUATION="1",
            COPILOT_SERVICE_SECRET=secrets.token_hex(32),
            COPILOT_STORE_ORIGIN=STORE,
            COPILOT_PANEL_ORIGIN=PANEL,
            COPILOT_STORE_PRIVATE_URL="http://127.0.0.1:4000",
            COPILOT_CATALOGUE_DB=str(DIR / "catalogue.sqlite"),
        )
        node = shutil.which("node")
        command(
            [
                node,
                "store/node_modules/tsx/dist/cli.mjs",
                "store/scripts/catalogue-import.ts",
                "--database",
                str(DIR / "catalogue.sqlite"),
            ],
            env=env,
        )
        start(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "agent.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            env,
            "agent",
        )
        start([node, "store/node_modules/tsx/dist/cli.mjs", "store/src/server.ts"], env, "store")
        (DIR / "mode.txt").write_text("strict")
        start([node, str(Path(__file__).with_name("cap04_https_proxy.mjs"))], env, "proxy")
        for port in (4000, 8000, 4443):
            wait_port(port)
        with sync_playwright() as pw:
            test(IsolatedBrowsers(pw, args.channel))
        RESULT["outcome"] = "passed"
    except Exception as error:
        RESULT["outcome"] = "failed"
        RESULT["error"] = str(error)[:1600]
        raise
    finally:
        cleanup(PROCESSES, thumb, TLS, DIR / f"result-{args.channel}.json", RESULT)


if __name__ == "__main__":
    main()
