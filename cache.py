import redis
import gzip
import json
import uuid
import os
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings

load_dotenv()

os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings()

# id generator for metadata
def generate_id():
    """
    Generate a unique integer ID
    """
    return uuid.uuid4().int

# Creating FAISS Cache
docs = [Document(
    page_content=" ",
    metadatas={
        "id": generate_id()
    })]

faiss_cache = FAISS.from_documents(docs, embeddings)

# Creating Redis Cache
redis_cache = redis.StrictRedis(host='localhost', port=6379, db=0)
ttl = 60 * 60 * 24  # 24 hours


# Caching Function
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

# Retrieve Cached data from Redis
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

# FAISS Similarity Search
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

    