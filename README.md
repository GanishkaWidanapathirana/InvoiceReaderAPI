# FastAPI Llama-Gemini Integration

This project demonstrates the integration of FastAPI with LlamaIndex, LlamaHub, and Gemini for analyzing PDFs and images.

## Features
- Accepts PDF and image files as input
- Processes documents using LlamaHub loaders (PDF and Image readers)
- Uses Gemini LLM for embedding and querying
- Stores temporary uploads for processing

## Setup Instructions
1. Clone the repository and navigate to the project directory.
2. Install dependencies using `pip install -r requirements.txt`.
3. Set up the `.env` file with your Gemini API details.
4. Run the server with `uvicorn app.main:app --reload`.

## API Endpoint
### `POST /analyze`
- **Input**: A PDF or image file and `user_type` (string).
- **Output**: Summary of the document content.

## Notes
- Ensure your Gemini API key and endpoint are valid.
- Temporary uploads are stored in the `uploads/` folder and automatically deleted after processing.
