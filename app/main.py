from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware

from app.services.analyze import process_invoice, load_document_by_id_and_create_index, \
    get_chat_query_response
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()
app = FastAPI()
print("App started")
# Access the API key from the environment
API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_CLOUD_API_KEY is not set in the .env file.")
# Define the origins you want to allow. For example, localhost:10000 is your frontend.
origins = [
    "http://localhost:10000",  # Allow your frontend
    "http://localhost",  # Allow localhost without port
    "https://localhost:10000",  # Allow secure localhost
    # You can add more origins here as needed
]

# Add the CORSMiddleware to your FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins or you can specify more
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.post("/upload")
async def upload_invoice(
        file: UploadFile = File(...),
        user_type: str = Form(...),  # "vendor" or "buyer"
):
    try:
        response = await process_invoice(file, user_type)
        return JSONResponse(content={"response": response})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/ask_chat")
async def ask_chat(query: str = Form(...), doc_id: str = Form(...)):
    """Endpoint to handle chat queries and return full response as JSON."""

    try:
        # Load the document index
        index = load_document_by_id_and_create_index(doc_id)

        # Get the response from the chat engine
        full_response = await get_chat_query_response(index, query)

        # Return the response as JSON
        return JSONResponse(content={"response": full_response})

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")