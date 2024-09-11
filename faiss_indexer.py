import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os

class FaissIndexer:
    """
    A class to create, search and save/load a FAISS index for text search using Sentence Transformers.
    """

    def __init__(self):
        """
        Initialize FaissIndexer class.
        """
        self.model = SentenceTransformer(os.environ["FAISS_EMBEDDING_MODEL"])
        self.index = None
        self.queries = []

    def build_index(self):
        """
        Builds the FAISS index.
        """
        d = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(d)

    def search_index(self, query_text, k=5):
        """
        Searches the FAISS index for the most similar queries to the query_text.

        :param query_text: The query text to search for in the index
        :param k: The number of top results to return (default: 5)
        :return: distance, index and query of most similar query
        """
        query_embedding = [self.model.encode(query_text)]
        query_embedding = np.array(query_embedding).astype('float32')
        D, I = self.index.search(query_embedding, k)
        search_result =self.queries[I[0][0]]
        return D[0], I[0], search_result


    def save_index(self, index_name):
        """
        Saves the FAISS index and the associated queries to files.

        :param index_name: The name of the index to be saved
        """
        index_filename = f"{index_name}.index"
        faiss.write_index(self.index, index_filename)
        with open(f"{index_name}_queries.json", 'w') as outfile:
            json.dump(self.queries, outfile)

    @classmethod
    def load_index(cls, index_name):
        """
        Loads a FAISS index.

        :param index_name: The name of the index to be loaded
        :return: An instance of FaissIndexer class with the loaded index, or None if an error occurs
        """
        try:
            index_filename = f"{index_name}.index"
            index = faiss.read_index(index_filename)
            with open(f"{index_name}_queries.json", 'r') as infile:
                queries = json.load(infile)
            indexer = cls()
            indexer.index = index
            indexer.queries = queries
            return indexer  # Return the instance of FaissIndexer with the loaded index
        except Exception as e:
            return None  # Return None if there was an error loading the index
        
    def store_query_in_faiss(self, query):
        """
        Store query embedding in faiss.

        :param query: The query that should be stored
        """
        embeddings = [self.model.encode(query)]
        embeddings = np.array(embeddings).astype('float32')
        self.queries.append(query)
        self.index.add(embeddings)