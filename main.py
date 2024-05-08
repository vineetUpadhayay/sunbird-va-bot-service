from dotenv import load_dotenv
import os
import time
from langchain_community.vectorstores import Marqo
import google.generativeai as genai 
import marqo
# from cache import pubsub
from cache import faiss_search, cache_in_redis

load_dotenv()

marqo_url = os.getenv("MARQO_URL")
db = marqo.Client(url=marqo_url)
index_name = os.getenv("MARQO_INDEX_NAME")



genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_content(res):
    """Helper to format Marqo's documents into text to be used as page_content"""
    return f"{res['page_content']}"

docsearch = Marqo(db, index_name=index_name, page_content_builder=get_content)

def marqo_search(query):
    docs = docsearch.similarity_search_with_score(query, k = 4)
    return docs

def get_context(docs):
    context = ""
    for doc in docs:
        context += f"context: {doc[0].page_content}"
    return context


def main():

    #pubsub.run_in_thread(sleep_time=0.01)

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
            docs = marqo_search(query)
            context = get_context(docs)
            print("\nNo cache hit. Retrieved from Marqo db \n")

        if context:
            prompt = f"""Answer the question as detailed as possible from the provided context\n\n
            Context:\n {context}?\n
            Question: \n{query}\n

            Answer:"""
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            response = response.text

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f'Question: {query}')
        print(f'Answer: {response[:100]}...')
        print(f'Time: {elapsed_time}')

        if not faiss_response:
            cache_in_redis(query, response, context)

    

if __name__ == '__main__':
  main()
