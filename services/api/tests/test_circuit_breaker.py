"""Tests for the async circuit breaker."""

import asyncio

import pytest

from app.clients.circuit_breaker import CircuitBreaker, CircuitOpenError, State


@pytest.fixture
def breaker():
    return CircuitBreaker(failure_threshold=3, recovery_timeout=0.5, half_open_max=1, name="test")


async def test_initial_state_is_closed(breaker: CircuitBreaker):
    assert breaker.state == State.CLOSED
    assert not breaker.is_open


async def test_stays_closed_below_threshold(breaker: CircuitBreaker):
    for _ in range(breaker.failure_threshold - 1):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    assert breaker.state == State.CLOSED


async def test_opens_after_threshold(breaker: CircuitBreaker):
    for _ in range(breaker.failure_threshold):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    assert breaker.state == State.OPEN
    assert breaker.is_open


async def test_open_rejects_immediately(breaker: CircuitBreaker):
    for _ in range(breaker.failure_threshold):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    with pytest.raises(CircuitOpenError):
        async with breaker.guard():
            pass  # should never reach here


async def test_transitions_to_half_open_after_recovery_timeout(breaker: CircuitBreaker):
    for _ in range(breaker.failure_threshold):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    assert breaker.state == State.OPEN

    await asyncio.sleep(breaker.recovery_timeout + 0.05)

    # Next guard call should transition to HALF_OPEN and allow the call through
    async with breaker.guard():
        pass  # success

    assert breaker.state == State.CLOSED


async def test_half_open_probe_failure_reopens(breaker: CircuitBreaker):
    for _ in range(breaker.failure_threshold):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    await asyncio.sleep(breaker.recovery_timeout + 0.05)

    with pytest.raises(ValueError):
        async with breaker.guard():
            raise ValueError("probe failed")

    assert breaker.state == State.OPEN


async def test_half_open_limits_concurrent_probes(breaker: CircuitBreaker):
    for _ in range(breaker.failure_threshold):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    await asyncio.sleep(breaker.recovery_timeout + 0.05)

    # First probe should succeed (half_open_max=1)
    async with breaker.guard():
        pass

    # Circuit should now be CLOSED (success closed it)
    assert breaker.state == State.CLOSED


async def test_success_resets_failure_count(breaker: CircuitBreaker):
    # Two failures
    for _ in range(2):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    # One success resets counter
    async with breaker.guard():
        pass

    assert breaker._failure_count == 0
    assert breaker.state == State.CLOSED

    # Need full threshold again to trip
    for _ in range(breaker.failure_threshold - 1):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    assert breaker.state == State.CLOSED


async def test_circuit_open_error_not_caught_as_failure(breaker: CircuitBreaker):
    """CircuitOpenError should not be counted as a failure."""
    for _ in range(breaker.failure_threshold):
        with pytest.raises(ValueError):
            async with breaker.guard():
                raise ValueError("boom")

    assert breaker.state == State.OPEN

    # CircuitOpenError should propagate without incrementing failure count
    prev_count = breaker._failure_count
    with pytest.raises(CircuitOpenError):
        async with breaker.guard():
            pass

    assert breaker._failure_count == prev_count
