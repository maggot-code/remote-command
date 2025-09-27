import time
import functools
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

# 令牌桶Lua脚本，保证原子性
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call("HMGET", key, "tokens", "timestamp")
local tokens = tonumber(bucket[1]) or capacity
local last_time = tonumber(bucket[2]) or now

local delta = math.max(0, now - last_time)
tokens = math.min(capacity, tokens + delta * refill_rate)
if tokens < requested then
    redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
    redis.call("EXPIRE", key, 60)
    return 0
else
    tokens = tokens - requested
    redis.call("HMSET", key, "tokens", tokens, "timestamp", now)
    redis.call("EXPIRE", key, 60)
    return 1
end
"""

def redis_token_bucket_limit(
    bucket_key,
    capacity=5,
    refill_rate=1,
    wait_timeout=30,
    sleep_interval=0.2,
    err_msg="服务器繁忙，请稍后重试"
):
    """
    Redis令牌桶限流装饰器，适用于Django接口并发控制。
    :param bucket_key: Redis中桶的唯一key
    :param capacity: 桶容量（最大突发并发数）
    :param refill_rate: 每秒补充令牌数（平均速率）
    :param wait_timeout: 最大等待时间（秒）
    :param sleep_interval: 等待重试间隔（秒）
    :param err_msg: 超时返回的错误信息
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            start = time.time()
            client = cache.client.get_client()
            key = f"bucket:{bucket_key}"
            while True:
                now = int(time.time())
                try:
                    allowed = client.eval(
                        TOKEN_BUCKET_LUA, 1, key, capacity, refill_rate, now, 1
                    )
                except Exception:
                    return Response({"error": "限流服务异常"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                if allowed == 1:
                    break
                if time.time() - start > wait_timeout:
                    return Response({"error": err_msg}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                time.sleep(sleep_interval)
            try:
                return func(self, request, *args, **kwargs)
            finally:
                pass  # 令牌桶无需释放
        return wrapper
    return decorator

def redis_concurrency_limit(semaphore_key, max_concurrent=5, wait_timeout=30):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            start = time.time()
            acquired = False
            while True:
                try:
                    current = cache.incr(semaphore_key, ignore_key_check=True)
                except Exception:
                    # 如果key不存在，初始化为1
                    cache.set(semaphore_key, 1, timeout=60)
                    current = 1
                if current == 1:
                    # 第一次设置时，设置一个过期时间，防止死锁
                    cache.expire(semaphore_key, 60)
                if current <= max_concurrent:
                    acquired = True
                    break
                else:
                    cache.decr(semaphore_key)
                    if time.time() - start > wait_timeout:
                        return Response({"error": "服务器繁忙，请稍后重试"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                    time.sleep(0.2)
            try:
                return func(self, request, *args, **kwargs)
            finally:
                if acquired:
                    cache.decr(semaphore_key)
        return wrapper
    return decorator