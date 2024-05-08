import os
from fastapi import HTTPException, APIRouter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from redisvl.extensions.llmcache import SemanticCache
from app.schema import model
from dotenv import load_dotenv

router = APIRouter()

# Load environment variables from .env file
load_dotenv()

# Retrieve OpenAI API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")

# Load FAISS index and model outside of the endpoint
embeddings = HuggingFaceEmbeddings()
new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization="True")
retriever = new_db.as_retriever()
llm = OpenAI(openai_api_key=openai_api_key)

# Initialize SemanticCache
llmcache = SemanticCache(
    name="llmcache",  # underlying search index name
    prefix="llmcache",  # redis key prefix for hash entries
    redis_url="redis://localhost:6379",  # redis connection url string
    distance_threshold=0.1  # semantic cache distance threshold
)


# Define endpoint to handle incoming queries
@router.post("/query/")
async def query_endpoint(request: model.QueryRequest):
    try:
        # Extract query from request
        query = request.query

        # Check the cache first
        cached_response = llmcache.check(prompt=query)
        if cached_response:
            return {"answer": cached_response[0]["response"]}

        # Retrieve context based on query
        docs = retriever.invoke(query)
        context = docs[0].page_content

        # Construct prompt template as a string representation
        template_with_context = f"""
        Use the following pieces of context to answer the question at the end:

        {context}

        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Use three sentences maximum and keep the answer as concise as possible.
        Always say "thanks for asking!" at the end of the answer.

        Question: {{query}}

        Helpful Answer:
        """

        # Chain the prompt template with the OpenAI model
        llm_chain_with_context = PromptTemplate.from_template(template_with_context) | llm

        # Invoke the model with the query
        result = llm_chain_with_context.invoke(query)

        # Store the result in the cache
        llmcache.store(
            prompt=query,
            response=result,

        )

        # Return the result
        return {"answer": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
