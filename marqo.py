import asyncio
import aioredis
import os
import marqo

# Initialize Marqo client
mq = marqo.Client(url='http://localhost:8882')

async def main():
    redis = await aioredis.create_redis_pool('redis://other_host:6379')
    keys = await redis.keys('*')
    values = []
    for key in keys:
        value = await redis.get(key)
        values.append(value)
        print(f'Key: {key}, Value: {value}')
    redis.close()
    await redis.wait_closed()

    l = 0
    for i, value in enumerate(values):
        pages = value.split(b"\n\n")
        for j, page_content in enumerate(pages):
            index_name = f"_page_{i+1}_{j+1}"
            mq.create_index(index_name)
            mq.index(index_name).add_documents([
                {"Content": page_content.decode()}  # Decoding to make it string
            ], tensor_fields=["Content"])
            l += 1
            
    results = []
    for index in range(l):
        result = index.search("History", search_method="LEXICAL")
        results.append(result)

asyncio.run(main())

