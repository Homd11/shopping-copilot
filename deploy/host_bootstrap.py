"""Explicit pre-loop host assembly. No import-time or environment-selected activation."""

import asyncio
from contextlib import suppress
from inspect import iscoroutinefunction
from pathlib import Path
from time import time

from agent.admission.async_runtime import AsyncAdmissionPolicy
from agent.admission.dynamodb import DynamoInvitationStore
from agent.app import create_app
from agent.catalogue_client import CatalogueClient
from agent.lifecycle.async_work import AsyncLifecycleWork
from agent.lifecycle.dynamodb import DynamoLifecycle
from agent.lifecycle.host_health import HostReadiness
from agent.lifecycle.lambda_runtime import _sdk
from agent.lifecycle.store import LifecycleUnavailable
from agent.storefront_service import StorefrontService, identity_config
from deploy.host_checks import HostChecks, unqualified_provider
from deploy.host_config import HostSettings


class _OwnedAdmission(AsyncAdmissionPolicy):
    def __init__(self, store, **limits):
        super().__init__(store, **limits)
        self._sdk, self._sdk_closed = store.client, False
        self._closing = None
        self._work = None

    async def _drain(self):
        while True:
            try:
                if self._work is not None:
                    await self._work.close()
                await super().close()
                break
            except asyncio.CancelledError:
                # Even cancellation during loop shutdown cannot advance SDK close.
                continue
        if not self._sdk_closed:
            self._sdk_closed = True
            with suppress(Exception):
                await asyncio.to_thread(self._sdk.close)

    async def close(self):
        if self._closing is None:
            self._closing = asyncio.create_task(self._drain())
            self._closing.add_done_callback(_ProviderGate._done)
        await asyncio.shield(self._closing)


class _ProviderGate:
    def __init__(self, verify):
        self._verify, self._flight, self._closed = verify, None, False

    @staticmethod
    def _done(task):
        if not task.cancelled():
            task.exception()

    async def ready(self):
        if self._closed or self._flight is not None and not self._flight.done():
            return False
        task = self._flight = asyncio.create_task(self._verify())
        task.add_done_callback(self._done)
        try:
            done, _ = await asyncio.wait({task}, timeout=1)
            return (
                task in done and not task.cancelled() and task.result() is True and not self._closed
            )
        except Exception:
            return False
        finally:
            if not task.done():
                task.cancel()

    async def close(self):
        self._closed = True
        if self._flight is not None:
            if not self._flight.done():
                self._flight.cancel()
            await asyncio.shield(asyncio.gather(self._flight, return_exceptions=True))


class _QualifiedWork(AsyncLifecycleWork):
    def __init__(self, lifecycle, sessions, provider):
        super().__init__(lifecycle, sessions)
        self._provider = provider

    async def check(self):
        generation = self.generation
        if not await self._provider.ready():
            raise LifecycleUnavailable()
        # Qualification is outside the actor lock. Pending renewal never waits on it.
        await super().check()
        if self.failed or self.generation != generation or self._provider._closed:
            raise LifecycleUnavailable()

    async def begin(self):
        await self.check()
        return await super().begin()

    async def close(self):
        try:
            await self._provider.close()
        finally:
            await super().close()


class _OwnedReadiness(HostReadiness):
    def __init__(self, work, settings, checks, provider):
        super().__init__(
            work, settings.readiness_secret, settings.fingerprint, checks.checks(provider)
        )
        self.checks_owner = checks

    async def close(self):
        try:
            await super().close()
        finally:
            await self.checks_owner.close()


def _runtime_root():
    return Path(__file__).resolve().parents[1]


def create_host_app(
    settings,
    *,
    sdk_factory=_sdk,
    provider_ready=unqualified_provider,
    model_client=None,
    http_transport=None,
    clock=time,
):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise ValueError("Host startup refused")
    sdk, admission, service, work, checks, readiness = None, None, None, None, None, None
    try:
        if type(settings) is not HostSettings or not iscoroutinefunction(provider_ready):
            raise ValueError()
        settings._validate()
        if _runtime_root() != settings.release:
            raise ValueError()
        sdk = sdk_factory("dynamodb")
        store = DynamoInvitationStore(
            sdk, settings.table, settings.namespace, settings.invitation_identity, clock=clock
        )
        lifecycle = DynamoLifecycle(store, settings.lifecycle_identity, clock=clock)
        admission = _OwnedAdmission(store, **settings.admission_limits)
        values = settings.environment()
        service = StorefrontService(identity_config(values), environment=values)
        provider = _ProviderGate(provider_ready)

        def work_factory(lifecycle, sessions):
            nonlocal work
            work = _QualifiedWork(lifecycle, sessions, provider)
            admission._work = work
            return work

        def readiness_factory(app, work):
            nonlocal checks, readiness
            checks = HostChecks(
                release=settings.release,
                fingerprint=settings.fingerprint,
                catalogue=settings.catalogue,
                admission=admission,
                guard=app.state.llm_client,
                service=service,
                transport=http_transport,
            )
            readiness = _OwnedReadiness(work, settings, checks, provider.ready)
            return readiness

        return create_app(
            environment=values,
            llm_client=model_client,
            admission=admission,
            lifecycle=lifecycle,
            lifecycle_work_factory=work_factory,
            readiness_factory=readiness_factory,
            storefront_service=service,
            catalogue_client=CatalogueClient(
                secret=settings.service_secret, transport=http_transport
            ),
            catalogue_retrieval_enabled=True,
        )
    except Exception:
        pass

    async def cleanup():
        for resource in (readiness, checks, work, admission):
            if resource is not None:
                with suppress(Exception):
                    await resource.close()
        if admission is None and sdk is not None:
            with suppress(Exception):
                await asyncio.to_thread(sdk.close)
        if service is not None:
            with suppress(Exception):
                await service.aclose()

    asyncio.run(cleanup())
    raise ValueError("Host startup refused")
