import redis
import gzip
import json
import uuid
import os, time
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def generate_id():
    """
    Generate a unique integer ID
    """
    return uuid.uuid4().int

docs = [Document(
    page_content=" ",
    metadatas={
        "id": generate_id()
    })]

faiss_cache = FAISS.from_documents(docs, embeddings)

redis_cache = redis.StrictRedis(host='localhost', port=6379, db=0)
ttl = 60 * 60 * 24  # 24 hours

def cache_in_redis(query, response, documents):
    """
    Cache the query, response and documents in Redis
    """
    id = generate_id()
    data = {
        "response": response,
        "documents": documents,
        "id": id
    }
    data = json.dumps(data)
    data = gzip.compress(data.encode("utf-8"))
    redis_cache.set(query, data, ttl)
    faiss_cache.add_documents([Document(page_content=query, metadatas={"id": id})])

def get_from_redis(query):
    """
    Get the query, response and documents from Redis
    """
    data = redis_cache.get(query)
    if data is None:
        return None
    data = gzip.decompress(data).decode("utf-8")
    data = json.loads(data)
    return data

def faiss_search(query):
    """
    Search for similar documents in FAISS
    """
    docs = faiss_cache.similarity_search_with_score(query)
    doc, score = docs[0]
    if(score <= 0.07):
        return {"response":get_from_redis(doc.page_content)["response"],"is_response": 1}
    elif(score <= 0.2):
        return {"documents":get_from_redis(doc.page_content)["documents"],"is_response": 0}
    else:
        return None

# def handle_expiration_event(message):
#     try:
#         print(message['data'])
#         expired_key = message['data'].decode('utf-8')
#         print(f'Redis Key {expired_key} expired')
#         compressed_expired_value = redis_cache.get(expired_key)
#         print(f'Value: {compressed_expired_value}')
#         expired_value = gzip.decompress(compressed_expired_value)
#         print(f'Decoded Value: {expired_value}')
#         data = json.loads(expired_value.decode('utf-8'))
#         print(f'JSON Data: {data}')
#         faiss_id = data['id']
#         faiss_cache.delete(faiss_id)
#         print(f'Redis Key {expired_key} expired, removed from Faiss cache')
#     except Exception as e:
#         print(f'Error: {e}')

# pubsub = redis_cache.pubsub()
# redis_cache.config_set('notify-keyspace-events', 'Ex')
# pubsub.psubscribe(**{"__keyevent@0__:expired": handle_expiration_event})

    