from dotenv import load_dotenv
import os
import time
from langchain_community.vectorstores import Marqo
import marqo
from cache import faiss_search, cache_in_redis
from openai import OpenAI

load_dotenv()

# Open AI client creation
os.environ["OPENAI_API_KEY"]=os.getenv("OPENAI_API_KEY")
client = OpenAI()

# Marqo client creation
marqo_url = os.getenv("MARQO_URL")
db = marqo.Client(url=marqo_url)
index_name = os.getenv("MARQO_INDEX_NAME")

def get_content(res):
    """Helper to format Marqo's documents into text to be used as page_content"""
    return f"{res['page_content']}"

# Creating searching object in Marqo db
docsearch = Marqo(db, index_name=index_name, page_content_builder=get_content)

# Converting Documents to context for LLM
def get_context(docs):
    context = ""
    for doc in docs:
        context += f"context: {doc[0].page_content}"
    return context


def main():
    queries = ["Tell me something about Hogwarts",
               "Say something about Hogwarts",
               "Tell me about Hogwarts in 20 words",
               "Tell me something about Quiddich"]

    for query in queries:

        print("#"*80)
        start_time = time.time()

        faiss_response = faiss_search(query)
        context = ""
        response = ""

        if faiss_response:
            print("Cache hit")
            if faiss_response['is_response']==0:
                context = faiss_response['documents']
                print("Documents found in cache \n")
            else:
                response= faiss_response['response']
                print("Response found in cache \n")
        else:
            docs = docsearch.similarity_search_with_score(query, k = 4)
            context = get_context(docs)
            print("\nNo cache hit. Retrieved from Marqo db \n")

        if context:
            prompt = f"""Answer the question as detailed as possible from the provided context\n\n
            Context:\n {context}?\n
            """
            
            response = client.chat.completions.create(
                model = "gpt-3.5-turbo",
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ]
            )
            response = response.choices[0].message.content

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f'Question: {query}')
        print(f'Answer: {response[:100]}...')
        print(f'Time: {elapsed_time}')

        if not faiss_response:
            cache_in_redis(query, response, context)

if __name__ == '__main__':
  main()
