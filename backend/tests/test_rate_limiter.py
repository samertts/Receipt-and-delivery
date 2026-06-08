class TestMemoryRateLimiter:
    def test_allows_within_limit(self):
        from app.core.security import MemoryRateLimiter

        limiter = MemoryRateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert not limiter.is_rate_limited("test-key")

    def test_blocks_exceeding_limit(self):
        from app.core.security import MemoryRateLimiter

        limiter = MemoryRateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert not limiter.is_rate_limited("test-key-block")
        assert limiter.is_rate_limited("test-key-block")

    def test_independent_keys(self):
        from app.core.security import MemoryRateLimiter

        limiter = MemoryRateLimiter(max_requests=2, window_seconds=60)
        limiter.is_rate_limited("key-a")
        limiter.is_rate_limited("key-a")
        assert not limiter.is_rate_limited("key-b")
        assert limiter.is_rate_limited("key-a")
        assert not limiter.is_rate_limited("key-b")

    def test_window_resets(self):
        from app.core.security import MemoryRateLimiter
        import time

        limiter = MemoryRateLimiter(max_requests=2, window_seconds=1)
        limiter.is_rate_limited("reset-key")
        limiter.is_rate_limited("reset-key")
        assert limiter.is_rate_limited("reset-key")
        time.sleep(1.1)
        assert not limiter.is_rate_limited("reset-key")

    def test_redis_limiter_import(self):
        from app.core.security import RedisRateLimiter

        assert RedisRateLimiter is not None
