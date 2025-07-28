# This code creates a "smart search system" that understands meaning, not just keywords. 
# When someone asks about "stopping their plan," it knows to look for "cancellation" info because 
# it learned that these phrases mean similar things!

# Instead of python knowledge_base.py (starts fresh each time), the AI model itself (the 22 million parameters that understand language) 
# has to be loaded fresh into memory every single time you run Python.
# You'd have a web server that loads once and stays running:

# Import libraries we need
from langchain_community.document_loaders import DirectoryLoader, TextLoader  # To read text files from folders
from langchain.text_splitter import RecursiveCharacterTextSplitter  # To break long documents into smaller chunks
from langchain_huggingface import HuggingFaceEmbeddings  # To convert text into numbers (embeddings)
from langchain_chroma import Chroma  # Our "smart database" for storing and searching embeddings
import os

class KnowledgeBase:
    def __init__(self, persist_directory="./chroma_db"):
        # persist_directory = where we save our database on the computer
        self.persist_directory = persist_directory
        
        # This is our "text-to-numbers translator" 
        # It converts sentences into 384-dimensional number lists
        # Think of it like a universal translator that turns words into math
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",  # A pre-trained AI model
            model_kwargs={'device': 'cpu'}  # Use CPU instead of GPU (cheaper, slower but fine for us)
        )
        
        # This will hold our vector database once we create it
        self.vectorstore = None
        
    def load_documents(self, docs_path="./support_docs"):
        loader = DirectoryLoader(docs_path, glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        
        # Fix the problem ONCE during ingestion, not every query
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,    # Hard limit - guaranteed to fit in LLM context
            chunk_overlap=100, # Overlap to prevent cutting important info
            length_function=len
        )
        splits = text_splitter.split_documents(documents)
        return splits
        
    def create_vectorstore(self, documents):
        # This is where the magic happens!
        # Convert all our text chunks into embeddings and store them in ChromaDB
        self.vectorstore = Chroma.from_documents(
            documents=documents,           # Our text chunks
            embedding=self.embeddings,     # Our text-to-numbers translator
            persist_directory=self.persist_directory  # Where to save everything
        )
        # ChromaDB automatically saves to disk (no need for .persist() anymore)
        
    def load_vectorstore(self):
        # Load an existing database from disk (if we already created one)
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
    def search(self, query, k=3):
        # The main search function! This is what makes everything "smart"
        # query = what the user is asking about
        # k = how many similar documents to return (default: top 3 matches)
        
        if not self.vectorstore:
            # If database isn't loaded yet, load it first
            self.load_vectorstore()
            
        # Here's what happens under the hood:
        # 1. Convert user's query ("stop my plan") into numbers
        # 2. Compare those numbers to all stored document numbers  
        # 3. Find the most similar ones (using math/distance calculations)
        # 4. Return the original text of those similar documents
        return self.vectorstore.similarity_search(query, k=k)

# Test code - runs when you execute this file directly
if __name__ == "__main__":
    # Step 1: Create our knowledge base system
    kb = KnowledgeBase()

    # Only create if doesn't exist
    if not os.path.exists("./chroma_db"):
        print("Creating knowledge base...")
        # Step 2: Load all the support documents and break them into chunks
        docs = kb.load_documents()
        # Step 3: Convert everything to embeddings and store in ChromaDB
        kb.create_vectorstore(docs)
    else:
        print("Loading existing knowledge base...")
        kb.load_vectorstore()
    
    # Step 4: Test the search! 
    # Even though we search "cancel subscription", it should find relevant docs
    # about cancellation even if they use different words
    results = kb.search("How do I cancel subscription?")
    
    # Step 5: Show what we found
    for doc in results:
        print(f"Content: {doc.page_content}")      # The actual text that matched
        print(f"Source: {doc.metadata}")           # Which file it came from
        print("---")