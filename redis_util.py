import redis
import zlib
import pickle
import os

from utils import get_from_env_or_config

# Connect to Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 0)
REDIS_TTL = get_from_env_or_config('redis', 'ttl') # 12 hours (TTL in seconds)
redis_client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=int(REDIS_DB))

def store_messages_in_redis(key, message, ttl=int(REDIS_TTL)):
    """Compresses a message using gzip and stores it in Redis."""
    redis_key = f"msg_{key}"
    serialized_json = pickle.dumps(message)
    compressed_data = zlib.compress(serialized_json)
    redis_client.setex(redis_key, ttl, compressed_data)

def read_messages_from_redis(key):
    """Retrieves a compressed message from Redis and decompresses it."""
    redis_key = f"msg_{key}"
    compressed_data = redis_client.get(redis_key)
    if compressed_data:
        decompressed_data = zlib.decompress(compressed_data)
        return pickle.loads(decompressed_data)
    else:
        return []  # Handle the case where the key doesn't exis
    
def store_response_in_redis(key, response):
    mapping = {
        'response': response,
        'access_count': 0,
    }
    redis_client.hset(name=key, mapping=mapping)

def read_response_from_redis(key):
    try:
        redis_client.hincrby(key, 'access_count', 1)
        response = redis_client.hget(key, 'response')
        return response.decode('utf-8')
    except Exception as e:
        print(e)
        return None
    
def get_cache_data_from_redis(context):
    """Retrieves frequently asked queries and responses from Redis based on context"""
    pattern = f'{context}_cache_*'
    pattern_length = len(pattern)-1
    pattern = pattern.encode('utf-8')
    matches = []

    for key in redis_client.scan_iter(match=pattern):
        decoded_key = key.decode('utf-8')
        query = decoded_key[pattern_length:]
        try:
            access_count = int(redis_client.hget(key, 'access_count'))
            if (access_count > 10):
                response = redis_client.hget(decoded_key, 'response').decode('utf-8')
                matches.append((query, response))
        except Exception as e:
            pass
    return matches