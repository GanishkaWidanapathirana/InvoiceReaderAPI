from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.services.analyze import process_invoice
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
