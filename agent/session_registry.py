"""In-memory session lookup, inactivity expiry and browser-tab ownership."""

from collections.abc import Callable
from time import monotonic
from uuid import uuid4

from agent.session_state import LeaseConflict, Session, SessionExpired, SessionNotFound

SESSION_TTL_SECONDS = 30 * 60


class SessionRegistry:
    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._sessions: dict[str, Session] = {}
        self._expired_ids: set[str] = set()

    def create(self, tab_id: str | None = None) -> Session:
        session = Session(
            session_id=f"session-{uuid4().hex}",
            lease_tab_id=tab_id,
            last_activity_at=self._clock(),
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        if session_id in self._expired_ids:
            raise SessionExpired(session_id)
        try:
            session = self._sessions[session_id]
        except KeyError as error:
            raise SessionNotFound(session_id) from error
        if self._clock() - session.last_activity_at > SESSION_TTL_SECONDS:
            del self._sessions[session_id]
            self._expired_ids.add(session_id)
            raise SessionExpired(session_id)
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
