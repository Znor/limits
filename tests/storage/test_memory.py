import time

import hiro

from limits import RateLimitItemPerMinute, RateLimitItemPerSecond
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter, MovingWindowRateLimiter


class TestMemoryStorage:
    def setup_method(self):
        self.storage = MemoryStorage()

    def test_in_memory(self):
        with hiro.Timeline().freeze() as timeline:
            limiter = FixedWindowRateLimiter(self.storage)
            per_min = RateLimitItemPerMinute(10)
            for i in range(0, 10):
                assert limiter.hit(per_min)
            assert not limiter.hit(per_min)
            timeline.forward(61)
            assert limiter.hit(per_min)

    def test_fixed_window_clear(self):
        limiter = FixedWindowRateLimiter(self.storage)
        per_min = RateLimitItemPerMinute(1)
        limiter.hit(per_min)
        assert not limiter.hit(per_min)
        limiter.clear(per_min)
        assert limiter.hit(per_min)

    def test_moving_window_clear(self):
        limiter = MovingWindowRateLimiter(self.storage)
        per_min = RateLimitItemPerMinute(1)
        limiter.hit(per_min)
        assert not limiter.hit(per_min)
        limiter.clear(per_min)
        assert limiter.hit(per_min)

    def test_reset(self):
        limiter = FixedWindowRateLimiter(self.storage)
        per_min = RateLimitItemPerMinute(10)
        for i in range(0, 10):
            assert limiter.hit(per_min)
        assert not limiter.hit(per_min)
        self.storage.reset()
        for i in range(0, 10):
            assert limiter.hit(per_min)
        assert not limiter.hit(per_min)

    def test_expiry(self):
        with hiro.Timeline().freeze() as timeline:
            limiter = FixedWindowRateLimiter(self.storage)
            per_min = RateLimitItemPerMinute(10)
            for i in range(0, 10):
                assert limiter.hit(per_min)
            timeline.forward(60)
            # touch another key and yield
            limiter.hit(RateLimitItemPerSecond(1))
            time.sleep(0.1)
            assert per_min.key_for() not in self.storage.storage

    def test_expiry_moving_window(self):
        with hiro.Timeline().freeze() as timeline:
            limiter = MovingWindowRateLimiter(self.storage)
            per_min = RateLimitItemPerMinute(10)
            per_sec = RateLimitItemPerSecond(1)
            for _ in range(0, 2):
                for _ in range(0, 10):
                    assert limiter.hit(per_min)
                timeline.forward(60)
                assert limiter.hit(per_sec)
                timeline.forward(1)
                time.sleep(0.1)
                assert [] == self.storage.events[per_min.key_for()]
