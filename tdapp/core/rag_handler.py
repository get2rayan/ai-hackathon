from langchain_community.vectorstores import FAISS
import os
from langchain_openai import OpenAIEmbeddings
from tdapp.data.document_loader import JSONLoader
from langchain_core.documents import Document

index_path = "faiss_index"
db: FAISS = None
embeddings: OpenAIEmbeddings = OpenAIEmbeddings(model="text-embedding-3-small")


class RAGHandler:
    def __init__(self):
        self.index_path = index_path
        self.db = db
        self.embeddings = embeddings
        self.JsonLoader = JSONLoader()
        # Load the FAISS vector index upon initialization
        self.load_vector_index()

    
    def get_json_data_chunks(self)->list[Document]:
        docs:list[Document] = self.JsonLoader.get_json_data_as_semantic_text_document()
        return docs
    
    def retrieve_context(self, query: str) -> list:
        if self.db is None:
            print("FAISS index is not loaded.")
            return []
        docs = self.db.similarity_search(query, k=3)
        print(f"\nRAG retrieved_data: \n{[doc.page_content for doc in docs]}")
        return [doc.page_content for doc in docs]
        # return {"retrieved_data": [doc.page_content for doc in docs]}
            

    def save_vector_index(self):
        json_chunks = self.get_json_data_chunks()
        self.db = FAISS.from_documents(json_chunks, self.embeddings)
        self.db.save_local(self.index_path)
        print(f"FAISS index saved at {self.index_path}")

    def load_vector_index(self):
        if os.path.isdir(self.index_path) and os.path.exists(os.path.join(self.index_path, "index.faiss")):
            try:
                print("\nLoading existing FAISS index...")
                self.db =  FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Error loading FAISS index: {e}. Recreating the index...")
                self.save_vector_index()
        else:
            print("\nFAISS index not found. Creating a new index...")
            self.save_vector_index()
        
        if self.db is None:
            print("\nLoading FAISS from newly created index...")
            self.db =  FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)


if __name__ == "__main__":
    rag_handler = RAGHandler()
    # Example usage of the retrieve method
    # query = "I want to prepare an indian dish made of rice and chicken"
    query = "Suggest a recipe that can be made using the following ingredients: ['tomatoes', 'ground beef', 'onions', 'mango', 'apple', 'chicken', 'shrimp', 'avocado', 'fish', 'beef']"
    result = rag_handler.retrieve_context(query)
    print(result)

    # # similarity search with score
    # docs_with_score = rag_handler.db.similarity_search_with_score(
    #     query,
    #     k=3,
    #     score_threshold=1.0
    # )
    # print(f"\nTop {len(docs_with_score)} relevant documents for query '{query}':")
    # for i,(doc, score) in enumerate(docs_with_score, start=1):
    #     print(f"\nDocument {i} - Score: {score:.4f} \nContent preview: {doc.page_content[:200]}")