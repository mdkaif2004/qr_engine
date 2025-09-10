# main.py

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
import io

from schemas import QRCodeRequest
from qr_generator import generate_qr_code

# Initialize FastAPI app
app = FastAPI(
    title="QR Code Generator API",
    description="An API to generate standard or custom-shaped QR codes with logos.",
    version="1.0.0"
)

# --- Exception Handling ---
@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    """Handles ValueErrors, typically from image processing or download failures."""
    return JSONResponse(
        status_code=400,
        content={"detail": f"Bad Request: {exc}"},
    )

# --- API Endpoints ---
@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    A simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}


@app.post("/generate-qr", tags=["QR Code"])
async def generate_qr_endpoint(request: QRCodeRequest):
    """
    Generates a QR code image based on the provided parameters.

    - **qr_data**: The content to encode in the QR code (required).
    - **shape_url**: URL of a silhouette image to embed the QR code into (optional).
    - **logo_url**: URL of a logo to place in the center of the QR code (optional).

    Returns the generated QR code as a PNG image.
    """
    try:
        # Generate the QR code image using the core logic
        final_image = generate_qr_code(
            qr_data=request.qr_data,
            shape_url=str(request.shape_url) if request.shape_url else None,
            logo_url=str(request.logo_url) if request.logo_url else None
        )

        # Save the image to a bytes buffer
        buffer = io.BytesIO()
        final_image.save(buffer, format="PNG")
        buffer.seek(0)

        # Return the image as a response
        return Response(content=buffer.getvalue(), media_type="image/png")

    except Exception as e:
        # Catch-all for any other unexpected errors
        print(f"An internal error occurred: {e}") # Log the error for debugging
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred: {e}"
        )


# --- Run the application ---
if __name__ == "__main__":
    # Remember to use the port number you previously mentioned: 5001
    uvicorn.run(app, host="10.1.4.22", port=5001)
    