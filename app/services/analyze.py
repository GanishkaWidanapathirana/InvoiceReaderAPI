from dotenv import load_dotenv
from app.utils import save_file
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
import os
# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_CLOUD_API_KEY is not set in the environment.")

# Initialize Gemini
llm = Gemini(api_key=API_KEY)
embed_model = GeminiEmbedding(api_key=API_KEY)

# Hardcoded queries based on user type
HARD_CODED_QUERIES = {
    "vendor": "How much have I received from this invoice?",
    "buyer": "How much do I owe in this invoice?"
}


def process_invoice(uploaded_file, user_type: str):
    # Save the uploaded file to a temporary directory
    temp_dir = "data/temp_uploads"
    file_path = save_file(uploaded_file, destination_folder=temp_dir)

    # Validate user type
    if user_type not in HARD_CODED_QUERIES:
        raise ValueError("Invalid user type. Must be 'vendor' or 'buyer'.")

    # Use SimpleDirectoryReader to load the uploaded document
    documents = SimpleDirectoryReader(temp_dir).load_data()

    # Create a VectorStoreIndex using the document and Gemini embedding
    index = VectorStoreIndex.from_documents(documents, llm=llm, embed_model=embed_model)

    # Query the index with the hardcoded query
    query = HARD_CODED_QUERIES[user_type]
    query_engine = index.as_query_engine()
    response = query_engine.query(query)

    # Format the response based on user type
    if user_type == "vendor":
        return f"As a vendor, you received: {response}"
    elif user_type == "buyer":
        return f"As a buyer, you owe: {response}"
