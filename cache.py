import redis
import gzip
import json
import uuid

from langchain_community.vectorstores import FAISS
from langchain_community.document import Document
from google.generativeai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
docs = [Document(page_content="")]
faiss_cache = FAISS.from_documents(docs, embeddings)

redis_cache = redis.StrictRedis(host='localhost', port=6379, db=0)
ttl = 60*60*24  # 24 hours

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

def cache_in_faiss(query, id):
    """
    Cache the query and id in Faiss
    """
    pass

def generate_id():
    """
    Generate a unique integer ID
    """
    return uuid.uuid4().int