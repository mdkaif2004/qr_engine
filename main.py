# main.py

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import io
import requests
import uuid

from schemas import QRCodeRequest
from qr_generator import generate_qr_code

# --- Configuration for the Upload Service (no changes) ---
UPLOAD_API_URL = "http://10.1.4.23:8080/api/v1/upload"
BEARER_TOKEN = "hg643646f3t45kvtu35tf565"

# Initialize FastAPI app (no changes)
app = FastAPI(
    title="QR Code Generator API",
    description="An API to generate QR codes and upload them to a file service.",
    version="1.1.0"
)

@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    """Handles ValueErrors, typically from image processing or download failures."""
    return JSONResponse(
        status_code=400,
        content={"detail": f"Bad Request: {exc}"},
    )

@app.get("/health", tags=["Health Check"])
async def health_check():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "API is healthy. Age: 2Days, Body temperature: 36.5, Heart rate: 64, Respiratory rate: 15, SpO₂: 92, BMI: 20"}

@app.post("/generate-qr", tags=["QR Code"])
async def generate_qr_endpoint(request: QRCodeRequest):
    """
    Generates a QR code, uploads it to the internal file service,
    and returns the final Cloudinary URL.
    """
    try:
        # --- MODIFICATION: Pass the new dotType parameter ---
        final_image = generate_qr_code(
            qr_data=request.qr_data,
            shape_url=str(request.shape_url) if request.shape_url else None,
            logo_url=str(request.logo_url) if request.logo_url else None,
            dotType=request.dotType  # <<< PASS THE NEW FIELD HERE
        )
        # -------------------------------------------------------

        buffer = io.BytesIO()
        final_image.save(buffer, format="PNG")
        buffer.seek(0)

        headers = {'Authorization': f'Bearer {BEARER_TOKEN}'}
        filename = f"{uuid.uuid4()}.png"
        files = {'file': (filename, buffer, 'image/png')}

        upload_response = requests.post(UPLOAD_API_URL, headers=headers, files=files, timeout=15)
        upload_response.raise_for_status()
        
        upload_data = upload_response.json()
        cloudinary_url = upload_data.get("cloudinary_url")

        if not cloudinary_url:
            raise HTTPException(status_code=500, detail="Upload service did not return a 'cloudinary_url'.")

        return {"image_urls": cloudinary_url}

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to the file upload service: {e}"
        )
    except Exception as e:
        print(f"An internal error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred: {e}"
        )

# --- Run the application (no changes) ---
if __name__ == "__main__":
    uvicorn.run(app, host="10.1.4.22", port=5001)
    