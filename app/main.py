from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from app.services.analyze import process_invoice
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()
app = FastAPI()

# Access the API key from the environment
API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_CLOUD_API_KEY is not set in the .env file.")


@app.post("/upload/")
async def upload_invoice(
        file: UploadFile = File(...),
        user_type: str = Form(...),  # "vendor" or "buyer"
):
    try:
        response = await process_invoice(file, user_type)
        return JSONResponse(content={"response": response})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
