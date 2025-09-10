# qr_generator.py

import cv2
import numpy as np
from PIL import Image, ImageDraw
import qrcode
import requests
from io import BytesIO
from typing import Optional

# --- Helper function to download images (no changes) ---
def _download_image(url: str):
    """Downloads an image from a URL and returns a PIL Image object."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to download image from {url}: {e}")
    except IOError:
        raise ValueError(f"Failed to open image from {url}. The URL may not point to a valid image.")

# --- Shaped QR code logic (updated to handle logo placement) ---
def _get_best_black_bbox(image_pil: Image.Image):
    """Finds the bounding box of the largest black contour in a PIL Image."""
    open_cv_image = np.array(image_pil.convert("RGB"))[:, :, ::-1].copy()

    if image_pil.mode == 'RGBA':
        alpha = np.array(image_pil)[:, :, 3]
        white_bg = np.ones_like(open_cv_image, dtype=np.uint8) * 255
        img = np.where(alpha[:, :, None] > 0, open_cv_image, white_bg)
    else:
        img = open_cv_image

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None
    best_contour = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(best_contour)

def _create_dummy_qr_pattern(width, height, module_size=3, density=0.5):
    """Creates a randomized black and white grid to mimic QR code texture."""
    num_modules_x = width // module_size
    num_modules_y = height // module_size
    random_modules = (np.random.rand(num_modules_y, num_modules_x) < density).astype(np.uint8) * 255
    dummy_pattern = cv2.resize(random_modules, (width, height), interpolation=cv2.INTER_NEAREST)
    return Image.fromarray(dummy_pattern).convert("RGBA")

def create_shaped_qr(silhouette_pil: Image.Image, qr_data: str, side_scale=0.7, logo_pil: Optional[Image.Image] = None):
    """
    Generates a QR code within a silhouette's main black area, now with correct logo placement.
    """
    bbox = _get_best_black_bbox(silhouette_pil)
    if bbox is None:
        raise ValueError("No valid black area found in the silhouette!")

    x, y, w, h = bbox
    silhouette_pil = silhouette_pil.convert("RGBA")

    # High error correction is essential for logos
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_matrix = qr.get_matrix()
    num_modules = len(qr_matrix)

    qr_area_size = int(min(w, h) * side_scale)
    module_size = max(1, qr_area_size // num_modules)
    qr_actual_size = num_modules * module_size

    # Position of the actual QR code block within the silhouette
    pos_x = x + (w - qr_actual_size) // 2
    pos_y = y + (h - qr_actual_size) // 2

    # --- Masking & Pattern Application (no changes) ---
    silhouette_cv = np.array(silhouette_pil.convert("RGB"))[:, :, ::-1]
    gray_sil = cv2.cvtColor(silhouette_cv, cv2.COLOR_BGR2GRAY)
    _, original_black_mask = cv2.threshold(gray_sil, 100, 255, cv2.THRESH_BINARY_INV)
    qr_placement_mask = np.zeros_like(original_black_mask)
    cv2.rectangle(qr_placement_mask, (pos_x, pos_y), (pos_x + qr_actual_size, pos_y + qr_actual_size), 255, -1)
    dummy_fill_mask_cv = cv2.bitwise_and(original_black_mask, cv2.bitwise_not(qr_placement_mask))
    dummy_fill_mask_pil = Image.fromarray(dummy_fill_mask_cv).convert("L")

    # --- Image Composition ---
    dummy_pattern = _create_dummy_qr_pattern(silhouette_pil.width, silhouette_pil.height, module_size=module_size)
    final_image = Image.new("RGBA", silhouette_pil.size, "WHITE")
    final_image.paste(dummy_pattern, (0, 0), mask=dummy_fill_mask_pil)

    # Draw the QR modules
    draw = ImageDraw.Draw(final_image)
    for row_idx, row in enumerate(qr_matrix):
        for col_idx, cell in enumerate(row):
            if cell:
                x1, y1 = pos_x + col_idx * module_size, pos_y + row_idx * module_size
                x2, y2 = x1 + module_size, y1 + module_size
                draw.rectangle([x1, y1, x2, y2], fill="black")

    # --- NEW: Add logo to the center of the REAL QR code ---
    if logo_pil:
        logo_max_size = int(qr_actual_size * 0.25)
        logo_pil.thumbnail((logo_max_size, logo_max_size))
        
        # Position the logo in the middle of the qr_actual_size block
        logo_pos_x = pos_x + (qr_actual_size - logo_pil.width) // 2
        logo_pos_y = pos_y + (qr_actual_size - logo_pil.height) // 2
        
        final_image.paste(logo_pil, (logo_pos_x, logo_pos_y), logo_pil)

    return final_image

# --- Standard QR code logic (updated to handle logo) ---
def create_standard_qr(qr_data: str, size: int = 512, logo_pil: Optional[Image.Image] = None):
    """
    Generates a standard QR code, now with integrated logo placement.
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
    img = img.resize((size, size), Image.NEAREST)

    # Add logo if provided
    if logo_pil:
        qr_width, qr_height = img.size
        logo_max_size = int(qr_width * 0.25)
        logo_pil.thumbnail((logo_max_size, logo_max_size))
        
        logo_pos = ((qr_width - logo_pil.width) // 2, (qr_height - logo_pil.height) // 2)
        
        # Add a white background behind the logo for better scannability
        bg_size = (logo_pil.width + 10, logo_pil.height + 10)
        bg_pos = ((qr_width - bg_size[0]) // 2, (qr_height - bg_size[1]) // 2)
        background = Image.new('RGBA', bg_size, 'white')
        
        img.paste(background, bg_pos)
        img.paste(logo_pil, logo_pos, logo_pil)
    
    return img

# --- Main generation orchestrator (updated to pass logo correctly) ---
def generate_qr_code(
    qr_data: str,
    shape_url: Optional[str] = None,
    logo_url: Optional[str] = None
) -> Image.Image:
    """
    Orchestrates the QR code generation process, handling optional shape and logo.
    """
    logo_img = None
    # Only download logo if a valid URL is provided
    if logo_url:
        logo_img = _download_image(logo_url)

    # If a valid shape URL is provided, create a shaped QR
    if shape_url:
        silhouette_img = _download_image(shape_url)
        return create_shaped_qr(
            silhouette_pil=silhouette_img, 
            qr_data=qr_data, 
            logo_pil=logo_img
        )
    else:
        # Otherwise, create a standard QR
        return create_standard_qr(
            qr_data=qr_data, 
            logo_pil=logo_img
        )