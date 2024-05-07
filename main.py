from dotenv import load_dotenv
import os
import time
from langchain_community.vectorstores import Marqo
import google.generativeai as genai 
import marqo

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
    query = "Tell me something about garden gnomes"

    print("#"*60)

    start_time = time.time()
    
    docs = marqo_search(query)

    context = get_context(docs)

    prompt = f"""Answer the question as detailed as possible from the provided context\n\n
    Context:\n {context}?\n
    Question: \n{query}\n

    Answer:"""
    
    model = genai.GenerativeModel('gemini-pro')

    response = model.generate_content(prompt)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f'Question: {query}')
    print(f'answer: {response.text}')
    print(f'Time: {elapsed_time}')

    

if __name__ == '__main__':
  main()
