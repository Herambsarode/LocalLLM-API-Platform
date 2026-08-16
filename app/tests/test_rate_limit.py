import time
import pytest
from app.api.middleware.rate_limit import InMemoryRateLimiter


class TestInMemoryRateLimiter:
    def setup_method(self):
        self.limiter = InMemoryRateLimiter()

    def test_allow_within_limit(self):
        allowed, _ = self.limiter.check("key1", 5, 60)
        assert allowed is True

    def test_block_when_exceeded(self):
        for _ in range(5):
            allowed, _ = self.limiter.check("key2", 5, 60)
            assert allowed is True

        allowed, reset_time = self.limiter.check("key2", 5, 60)
        assert allowed is False
        assert reset_time > int(time.time())

    def test_different_keys_independent(self):
        for _ in range(5):
            self.limiter.check("key_a", 5, 60)

        allowed, _ = self.limiter.check("key_b", 5, 60)
        assert allowed is True

    def test_window_expires(self):
        for _ in range(5):
            self.limiter.check("key3", 5, 1)

        time.sleep(1.1)
        allowed, _ = self.limiter.check("key3", 5, 1)
        assert allowed is True

    def test_cleanup(self):
        self.limiter.check("old_key", 5, 60)
        self.limiter.requests["old_key"] = [time.time() - 7200]
        self.limiter.cleanup()
        assert "old_key" not in self.limiter.requests
