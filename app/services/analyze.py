import os
import json
import re
from datetime import datetime, time

import chromadb
from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_parse import LlamaParse

from app.database import schemas
from app.database.database import get_db
from app.models import models
from app.utils import save_file
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_CLOUD_API_KEY is not set in the environment.")
if not LLAMA_CLOUD_API_KEY:
    raise ValueError("LLAMA_CLOUD_API_KEY is not set in the environment.")

# Initialize Gemini
embed_model = GeminiEmbedding(api_key=GEMINI_API_KEY, model_name="models/embedding-001", )
llm = Gemini(model="models/gemini-1.5-flash", api_key=GEMINI_API_KEY)

# Initialize ChromaDB client
db = chromadb.PersistentClient(path="./chroma_db")


async def parse_invoice(file_path):
    """Handles both PDFs and images (JPEG, PNG) using LlamaParse."""

    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        result_type="markdown",
        verbose=True
    )

    # Define supported file types for LlamaParse
    file_extractor = {
        ".pdf": parser,  # PDF parsing (including OCR for scanned PDFs)
        ".jpeg": parser,  # Image OCR
        ".jpg": parser,
        ".png": parser
    }

    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in file_extractor:
        raise ValueError(f"Unsupported file type: {ext}")

    # Process the file with LlamaParse
    reader = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor)
    documents = await reader.aload_data()
    if not documents:
        raise ValueError("The uploaded PDF is empty or could not be parsed.")
    return documents  # Returns extracted text from PDF or image


async def query_llm(documents, user_type: str):
    """Queries LLM to analyze invoice details and generate suggestions."""
    # Set Global settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    print(documents)
    # Get document ID immediately after insertion
    new_doc_id = documents[0].id_  # Get the first document's unique ID
    # Create or get the collection
    chroma_collection = db.get_or_create_collection(new_doc_id)
    # Create a vector store with ChromaDB
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Store document in ChromaDB
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, llm=llm,
                                            embed_model=embed_model)
    query_engine = index.as_query_engine(llm=llm)

    # Get today's date in YYYY-MM-DD format
    current_date = datetime.today().strftime("%Y-%m-%d")
    # Ask LLM to extract invoice details and provide suggestions
    invoice_analysis_query = (
        'Extract the following invoice details and analyze them in relation to the current date ({current_date}): '
        '{{'
        '"invoice_number": "<invoice_number>", '
        '"amount": <amount>, '
        '"due_date": "<YYYY-MM-DD>", '
        '"payment_status": "<paid/overdue/pending>", '
        '"discount_rate": <rate>, '
        '"late_fee": <late_fee>, '
        '"grace_period": "<grace_period_if_any>", '
        '"vendor_name": "<vendor_name>", '
        '"buyer_name": "<buyer_name>" '
        '}} '
        'In addition to extracting these details, correctly identify and extract the following: '
        '- The **vendor name** associated with the invoice. '
        '- The **buyer name** associated with the invoice. '
        'Then, based on the comparison of due_date and current_date ({current_date}): '
        '- If the invoice is overdue, suggest relevant actions for the {user_type} (vendor or buyer). '
        '- If the invoice is due soon (within 5 days), suggest early payment incentives (for vendors) or extension requests (for buyers). '
        '- If the invoice is not due soon, suggest monitoring options. '
        'Only return suggestions and email body relevant to the **{user_type}**. '
        'Make sure to add suggestions and email body as JSON fields to above Json structure.Need only one structure. '
        'Make sure add only suggestions as list.as example [suggestion1,suggestion2,suggestion3]. no need another action part '
        'In the email body, address the user based on the role,Only need email body.: '
        '- If the user is a **buyer**, start the email with "Dear vendor_name" and sign off with "Best regards, your_name". '
        '- If the user is a **vendor**, start the email with "Dear buyer_name" and sign off with "Best regards, your_name". '
        'Ensure that the email tone is polite and professional based on the role (buyer or vendor). '
        'If the **vendor name** or **buyer name** is identified, use those names in the greeting; otherwise, use "Dear Vendor" or "Dear Buyer".'
    ).format(current_date=current_date, user_type=user_type)

    response = query_engine.query(invoice_analysis_query)
    return clean_json_response(response.response), new_doc_id


def clean_json_response(response_text: str):
    """Cleans and parses JSON response from the LLM."""
    cleaned_content = re.sub(r"^```json\n|\n```$", "", response_text.strip())
    try:
        return json.loads(cleaned_content)
    except json.JSONDecodeError:
        raise ValueError("Response from Gemini is not in the expected JSON format.")


def parse_invoice_response(response: dict, doc_id: str):
    try:
        # Ensure the response is a dictionary, if it's not a string
        if isinstance(response, str):
            parsed_response = json.loads(response)  # parse the JSON string into a dictionary
        else:
            parsed_response = response  # directly use the dictionary if it's already parsed

        # Ensure 'null' values are handled properly and set if any value is null
        parsed_response = {
            "document_id": doc_id,
            "invoice_number": parsed_response.get("invoice_number", None),
            "amount": parsed_response.get("amount", None),
            "due_date": parsed_response.get("due_date", None),
            "payment_status": parsed_response.get("payment_status", None),
            "discount_rate": parsed_response.get("discount_rate", None),
            "late_fee": parsed_response.get("late_fee", None),
            "grace_period": parsed_response.get("grace_period", None),
            "vendor_name": parsed_response.get("vendor_name", None),
            "buyer_name": parsed_response.get("buyer_name", None),
            "suggestions": parsed_response.get("suggestions", []),
            "email_body": parsed_response.get("email_body", None)
        }

        return parsed_response

    except json.JSONDecodeError:
        return {"error": "Invalid response format"}


def load_document_by_id_and_create_index(doc_id: str):
    """Find a document by its ID and create a vector index."""

    # Initialize ChromaDB client
    db2 = chromadb.PersistentClient(path="./chroma_db")

    # Retrieve or create the collection for the given doc_id
    chroma_collection2 = db2.get_or_create_collection(doc_id)

    if not chroma_collection2.get():  # Check if document exists
        raise ValueError(f"Document with ID {doc_id} not found.")

    # Create the vector store and index
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection2)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
        llm=llm  # Add the LLM here
    )

    return index


async def get_chat_query_response(index: VectorStoreIndex, question: str):
    """Query the vector index with a question and return the full response as a string."""

    query_engine = index.as_chat_engine(streaming=False, llm=llm)  # Disable streaming
    response = query_engine.chat(question)  # Get full response at once

    return response.response  # Return the full response text


def create_invoice(parsed_invoice, mysql_db: Session = Depends(get_db)):
    try:
        # Convert the parsed response to database model
        db_invoice = models.Invoice(
            document_id=parsed_invoice["document_id"],
            invoice_number=parsed_invoice["invoice_number"],
            amount=parsed_invoice["amount"],
            due_date=datetime.strptime(parsed_invoice["due_date"], "%Y-%m-%d").date() if parsed_invoice[
                "due_date"] else None,
            payment_status=parsed_invoice["payment_status"],
            discount_rate=parsed_invoice["discount_rate"],
            late_fee=parsed_invoice["late_fee"],
            grace_period=parsed_invoice["grace_period"],
            vendor_name=parsed_invoice["vendor_name"],
            buyer_name=parsed_invoice["buyer_name"],
            suggestions=parsed_invoice["suggestions"],
            email_body=parsed_invoice["email_body"]
        )
        mysql_db.add(db_invoice)
        mysql_db.commit()
        mysql_db.refresh(db_invoice)
        return db_invoice
    except Exception as e:
        mysql_db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


async def process_invoice(uploaded_file, user_type: str):
    """Main function to handle invoice processing and response formatting."""
    if user_type not in ["vendor", "buyer"]:
        raise ValueError("Invalid user type. Must be 'vendor' or 'buyer'.")

    # Save the uploaded file to a temporary directory
    temp_dir = "data/temp_uploads"
    file_path = save_file(uploaded_file, destination_folder=temp_dir)
    try:
        # Parse Invoice
        documents = await parse_invoice(file_path)

        # Query LLM step-by-step
        raw_responses, doc_id = await query_llm(documents, user_type)
        # Clean JSON Responses
        parsed_invoice = parse_invoice_response(raw_responses, doc_id)
        create_invoice(parsed_invoice,)
        return parsed_invoice
    finally:
        # Ensure the file is deleted after processing, even if an error occurs
        if os.path.exists(file_path):
            os.remove(file_path)
