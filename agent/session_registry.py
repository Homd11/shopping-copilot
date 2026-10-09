"""In-memory session lookup, inactivity expiry and browser-tab ownership."""

from collections.abc import Callable
from time import monotonic
from uuid import uuid4

from agent.session_state import LeaseConflict, Session, SessionExpired, SessionNotFound

SESSION_TTL_SECONDS = 30 * 60


class SessionRegistry:
    def __init__(self, *, clock: Callable[[], float] = monotonic, capacity: int = 800) -> None:
        self._clock = clock
        self._capacity = capacity
        self._sessions: dict[str, Session] = {}
        self._expired_ids: dict[str, float] = {}

    def _expire(self) -> None:
        now = self._clock()
        for key, session in list(self._sessions.items()):
            if now - session.last_activity_at > SESSION_TTL_SECONDS:
                del self._sessions[key]
                self._expired_ids[key] = now
        for key, expired_at in list(self._expired_ids.items()):
            if now - expired_at > SESSION_TTL_SECONDS:
                del self._expired_ids[key]
        while len(self._expired_ids) > self._capacity:
            del self._expired_ids[next(iter(self._expired_ids))]

    def create(self, tab_id: str | None = None) -> Session:
        self._expire()
        if len(self._sessions) >= self._capacity:
            raise OverflowError("Session capacity reached")
        session = Session(
            session_id=f"session-{uuid4().hex}",
            lease_tab_id=tab_id,
            last_activity_at=self._clock(),
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        self._expire()
        if session_id in self._expired_ids:
            raise SessionExpired(session_id)
        try:
            session = self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFound(session_id) from error
        return session

    def touch(self, session: Session) -> None:
        session.last_activity_at = self._clock()

    def assert_lease(self, session: Session, tab_id: str | None) -> None:
        if session.lease_tab_id is None:
            if tab_id is not None:
                session.lease_tab_id = tab_id
            return
        if tab_id != session.lease_tab_id:
            raise LeaseConflict("Another browser tab owns this Shopping Task")

    def takeover(self, session_id: str, tab_id: str) -> Session:
        session = self.get(session_id)
        session.lease_tab_id = tab_id
        self.touch(session)
        return session

    def owns_lease(self, session_id: str, tab_id: str | None) -> bool:
        session = self.get(session_id)
        return session.lease_tab_id is None or session.lease_tab_id == tab_id
