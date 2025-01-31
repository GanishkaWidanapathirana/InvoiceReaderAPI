import os
import json
import re
from datetime import datetime

from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_parse import LlamaParse
from app.utils import save_file

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

async def parse_invoice(file_path: str):
    """Parses the uploaded invoice using LlamaParse."""
    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        result_type="markdown",
        verbose=True
    )
    file_extractor = {".pdf": parser}
    reader = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor)

    documents = await reader.aload_data()
    if not documents:
        raise ValueError("The uploaded PDF is empty or could not be parsed.")

    return documents


async def query_llm(documents, user_type: str):
    """Queries LLM to analyze invoice details and generate suggestions."""
    index = VectorStoreIndex.from_documents(documents, llm=llm, embed_model=embed_model)
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
        'Make sure to add suggestions and email body as JSON fields. '
        'In the email body, address the user based on the role: '
        '- If the user is a **buyer**, start the email with "Dear vendor_name" and sign off with "Best regards, your_name". '
        '- If the user is a **vendor**, start the email with "Dear buyer_name" and sign off with "Best regards, your_name". '
        'Ensure that the email tone is polite and professional based on the role (buyer or vendor). '
        'If the **vendor name** or **buyer name** is identified, use those names in the greeting; otherwise, use "Dear Vendor" or "Dear Buyer".'
    ).format(current_date=current_date, user_type=user_type)

    response = query_engine.query(invoice_analysis_query)
    return clean_json_response(response.response)


def clean_json_response(response_text: str):
    """Cleans and parses JSON response from the LLM."""
    cleaned_content = re.sub(r"^```json\n|\n```$", "", response_text.strip())
    try:
        return json.loads(cleaned_content)
    except json.JSONDecodeError:
        raise ValueError("Response from Gemini is not in the expected JSON format.")


def parse_invoice_response(response: dict):
    try:
        # Ensure the response is a dictionary, if it's not a string
        if isinstance(response, str):
            parsed_response = json.loads(response)  # parse the JSON string into a dictionary
        else:
            parsed_response = response  # directly use the dictionary if it's already parsed

        # Ensure 'null' values are handled properly and set if any value is null
        parsed_response = {
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
            "email_body": parsed_response.get("email_body", {
                "subject": None,
                "body": None
            })
        }

        return parsed_response

    except json.JSONDecodeError:
        return {"error": "Invalid response format"}


async def process_invoice(uploaded_file, user_type: str):
    """Main function to handle invoice processing and response formatting."""
    if user_type not in ["vendor", "buyer"]:
        raise ValueError("Invalid user type. Must be 'vendor' or 'buyer'.")

    # Save the uploaded file to a temporary directory
    temp_dir = "data/temp_uploads"
    file_path = save_file(uploaded_file, destination_folder=temp_dir)

    # Parse Invoice
    documents = await parse_invoice(file_path)

    # Query LLM step-by-step
    raw_responses = await query_llm(documents, user_type)
    # Clean JSON Responses
    return parse_invoice_response(raw_responses)
