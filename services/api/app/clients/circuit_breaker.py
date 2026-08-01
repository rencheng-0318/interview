"""Lightweight async circuit breaker with three states: CLOSED, OPEN, HALF_OPEN."""

import asyncio
import enum
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

logger = logging.getLogger("api.circuit_breaker")


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is OPEN and rejects a request."""


class State(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Async circuit breaker that trips after consecutive failures.

    - CLOSED: normal operation; failures are counted.
    - OPEN: requests are rejected immediately with CircuitOpenError.
    - HALF_OPEN: a limited number of probe requests are allowed through;
      success closes the circuit, failure re-opens it.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max: int = 2
    name: str = "default"

    _state: State = field(default=State.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    @property
    def state(self) -> State:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == State.OPEN

    async def _maybe_transition_to_half_open(self) -> None:
        """If OPEN and recovery_timeout has elapsed, transition to HALF_OPEN."""
        if self._state != State.OPEN:
            return
        if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
            self._state = State.HALF_OPEN
            self._half_open_calls = 0
            logger.info(
                "circuit_breaker=%s state=HALF_OPEN (recovery_timeout elapsed)",
                self.name,
            )

    @asynccontextmanager
    async def guard(self):
        """Context manager that guards a code block.

        - OPEN: raises CircuitOpenError immediately.
        - HALF_OPEN: allows up to half_open_max calls; success closes the circuit.
        - CLOSED: counts failures; trips to OPEN after failure_threshold.
        """
        async with self._lock:
            await self._maybe_transition_to_half_open()

            if self._state == State.OPEN:
                raise CircuitOpenError(
                    f"circuit_breaker={self.name} is OPEN"
                )

            if self._state == State.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max:
                    raise CircuitOpenError(
                        f"circuit_breaker={self.name} HALF_OPEN probe limit reached"
                    )
                self._half_open_calls += 1

        try:
            yield
        except CircuitOpenError:
            raise
        except Exception as exc:
            await self._record_failure()
            raise exc
        else:
            await self._record_success()

    async def _record_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == State.HALF_OPEN:
                self._state = State.OPEN
                logger.warning(
                    "circuit_breaker=%s state=OPEN (half_open probe failed, failures=%d)",
                    self.name,
                    self._failure_count,
                )
            elif self._failure_count >= self.failure_threshold:
                self._state = State.OPEN
                logger.warning(
                    "circuit_breaker=%s state=OPEN (failures=%d >= threshold=%d)",
                    self.name,
                    self._failure_count,
                    self.failure_threshold,
                )

    async def _record_success(self) -> None:
        async with self._lock:
            if self._state == State.HALF_OPEN:
                logger.info(
                    "circuit_breaker=%s state=CLOSED (half_open probe succeeded)",
                    self.name,
                )
            self._state = State.CLOSED
            self._failure_count = 0
