# qr_generator.py

import cv2
import numpy as np
from PIL import Image, ImageDraw
import qrcode
import requests
from io import BytesIO
from typing import Optional, List

from qr_drawers import draw_module, draw_qr_from_matrix, _is_finder_pattern_module # <<< IMPORT _is_finder_pattern_module

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

# --- Shaped QR code logic (updated) ---
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


# qr_generator.py

# ... (all existing imports) ...

# --- NEW: Define the structure of a standard 7x7 QR finder pattern ---
# 1 represents a black module, 0 represents a white module.
_FINDER_PATTERN = np.array([
    [1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1],
], dtype=np.uint8)
# --------------------------------------------------------------------
#new

# # ... (rest of the file is unchanged until the function below) ...

# def _create_dummy_qr_pattern(width, height, module_size=3, density=0.5, dotType: Optional[str] = None):
#     """
#     Creates a randomized black and white grid to mimic QR code texture, 
#     now with proper finder patterns that include borders.
#     """
#     num_modules_x = width // module_size
#     num_modules_y = height // module_size
    
#     # 1. Start with a matrix of random modules based on density
#     module_matrix = (np.random.rand(num_modules_y, num_modules_x) < density).astype(np.uint8)

#     # 2. Add a few proper 7x7 finder patterns to the matrix
#     finder_size = 7  # The dimension of our finder pattern
#     # The patterns are large, so we add fewer of them.
#     num_finders = int((num_modules_x * num_modules_y) * 0.002) 

#     for _ in range(num_finders):
#         # Pick a random top-left corner, ensuring the pattern fits within the bounds
#         if (num_modules_y > finder_size) and (num_modules_x > finder_size):
#             rand_y = np.random.randint(0, num_modules_y - finder_size)
#             rand_x = np.random.randint(0, num_modules_x - finder_size)
            
#             # "Stamp" the pre-defined finder pattern onto the main matrix
#             module_matrix[rand_y:rand_y + finder_size, rand_x:rand_x + finder_size] = _FINDER_PATTERN

#     # 3. Draw the final image from the prepared matrix (this logic remains the same)
#     dummy_img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
#     draw = ImageDraw.Draw(dummy_img)

#     for r in range(num_modules_y):
#         for c in range(num_modules_x):
#             if module_matrix[r, c] == 1:  # If the module is black (1)
#                 x1 = c * module_size
#                 y1 = r * module_size
#                 box = (x1, y1, x1 + module_size, y1 + module_size)
#                 draw_module(draw, box, dotType)
#             # We don't need to handle '0' because the background is already transparent/white
    
#     return dummy_img

# # ... (rest of the file is unchanged) ...


def _create_dummy_qr_pattern(width, height, module_size=3, density=0.5, dotType: Optional[str] = None): # <<< ADD dotType
    """Creates a randomized black and white grid to mimic QR code texture with custom dotType."""
    num_modules_x = width // module_size
    num_modules_y = height // module_size
    
    dummy_img = Image.new("RGBA", (width, height), (255, 255, 255, 0)) # Start with transparent
    draw = ImageDraw.Draw(dummy_img)

    # Draw dummy modules using the custom dotType
    for r in range(num_modules_y):
        for c in range(num_modules_x):
            if np.random.rand() < density:
                x1 = c * module_size
                y1 = r * module_size
                box = (x1, y1, x1 + module_size, y1 + module_size)
                draw_module(draw, box, dotType) # <<< USE draw_module
    
    return dummy_img

def create_shaped_qr(silhouette_pil: Image.Image, qr_data: str, side_scale=0.7, logo_pil: Optional[Image.Image] = None, dotType: Optional[str] = None):
    """
    Generates a QR code within a silhouette, now with custom dot styles for non-finder patterns,
    and a logo that also respects the dotType.
    """
    bbox = _get_best_black_bbox(silhouette_pil)
    if bbox is None:
        raise ValueError("No valid black area found in the silhouette!")

    x, y, w, h = bbox
    silhouette_pil = silhouette_pil.convert("RGBA")

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_matrix = qr.get_matrix()
    num_modules = len(qr_matrix) # This is the internal QR matrix size

    qr_area_size = int(min(w, h) * side_scale)
    module_size = max(1, qr_area_size // num_modules)
    qr_actual_size = num_modules * module_size

    pos_x = x + (w - qr_actual_size) // 2
    pos_y = y + (h - qr_actual_size) // 2

    silhouette_cv = np.array(silhouette_pil.convert("RGB"))[:, :, ::-1]
    gray_sil = cv2.cvtColor(silhouette_cv, cv2.COLOR_BGR2GRAY)
    _, original_black_mask = cv2.threshold(gray_sil, 100, 255, cv2.THRESH_BINARY_INV)
    qr_placement_mask = np.zeros_like(original_black_mask)
    cv2.rectangle(qr_placement_mask, (pos_x, pos_y), (pos_x + qr_actual_size, pos_y + qr_actual_size), 255, -1)
    
    # Create the dummy pattern for the outer silhouette
    # Pass dotType to create the dummy pattern in the desired style
    dummy_pattern = _create_dummy_qr_pattern(
        silhouette_pil.width, silhouette_pil.height, 
        module_size=module_size, 
        dotType=dotType # <<< Pass dotType here
    )
    
    final_image = Image.new("RGBA", silhouette_pil.size, "WHITE")
    
    # Apply the silhouette as a mask to the dummy pattern
    # We need to create a mask where only the silhouette's black parts are visible,
    # and not where the main QR code will be placed.
    combined_mask = Image.fromarray(cv2.bitwise_and(original_black_mask, cv2.bitwise_not(qr_placement_mask))).convert("L")
    final_image.paste(dummy_pattern, (0, 0), mask=combined_mask)


    draw = ImageDraw.Draw(final_image)
    
    # Draw the main QR modules
    # Loop over the actual QR matrix modules
    for row_idx, row in enumerate(qr_matrix):
        for col_idx, cell in enumerate(row):
            if cell:
                # Coordinates on the final_image for the QR module
                x1 = pos_x + col_idx * module_size
                y1 = pos_y + row_idx * module_size
                box = (x1, y1, x1 + module_size, y1 + module_size)
                
                # Determine if this module is part of a finder pattern
                # For shaped QR, we assume border=0 for the actual QR matrix logic
                is_finder = _is_finder_pattern_module(row_idx, col_idx, num_modules, border=0) # <<< Check against QR matrix

                draw_module(draw, box, dotType, is_finder=is_finder)
    
    # --- NEW: Draw logo with custom dotType ---
    if logo_pil:
        logo_max_size = int(qr_actual_size * 0.25)
        logo_pil.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
        
        logo_pos_x = pos_x + (qr_actual_size - logo_pil.width) // 2
        logo_pos_y = pos_y + (qr_actual_size - logo_pil.height) // 2
        
        # Create a temporary canvas for the logo with dotType
        logo_canvas = Image.new("RGBA", logo_pil.size, (255,255,255,0))
        logo_draw = ImageDraw.Draw(logo_canvas)
        
        # Determine the effective module size for the logo based on its new size
        # This is a bit of an approximation for the logo itself
        logo_module_size_approx = min(logo_pil.width, logo_pil.height) // 7 # Approx 7x7 for logo area
        
        # Iterate over the logo's pixels/regions and draw "dots" for black parts
        # This part requires more thought to integrate dotType effectively without losing logo detail
        # For simplicity, we'll draw logo on a white circle/square background and then paste it
        # If the logo itself needs to be "dot-ified", that's a more complex image processing task
        
        # For now, let's keep the logo itself as is, but ensure it's on a clean background
        
        # Create a mask from the logo itself for clean pasting
        if logo_pil.mode == 'RGBA':
            logo_mask = logo_pil
        else:
            logo_mask = logo_pil.convert("RGBA")
        
        # Make a white background for the logo
        bg_logo_size = (logo_pil.width + 10, logo_pil.height + 10)
        bg_logo_img = Image.new("RGBA", bg_logo_size, "white")
        
        # Calculate position to center logo on its background
        logo_on_bg_x = (bg_logo_size[0] - logo_pil.width) // 2
        logo_on_bg_y = (bg_logo_size[1] - logo_pil.height) // 2
        
        bg_logo_img.paste(logo_pil, (logo_on_bg_x, logo_on_bg_y), logo_mask)
        
        # Now paste this combined background+logo onto the final image
        final_image.paste(bg_logo_img, 
                          (logo_pos_x - (bg_logo_size[0] - logo_pil.width) // 2, 
                           logo_pos_y - (bg_logo_size[1] - logo_pil.height) // 2), 
                          bg_logo_img)

    return final_image

# --- Standard QR code logic (updated) ---
def create_standard_qr(qr_data: str, size: int = 512, logo_pil: Optional[Image.Image] = None, dotType: Optional[str] = None):
    """
    Generates a standard QR code, now with custom dot styles for non-finder patterns,
    and a logo that also respects the dotType.
    """
    border = 2 # Standard border size for standard QR codes
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=border)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_matrix = qr.get_matrix()
    # Use our custom drawer that respects finder patterns
    img = draw_qr_from_matrix(qr_matrix, border=border, dotType=dotType, size=size)
    
    if logo_pil:
        qr_width, qr_height = img.size
        logo_max_size = int(qr_width * 0.25)
        logo_pil.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
        
        logo_pos = ((qr_width - logo_pil.width) // 2, (qr_height - logo_pil.height) // 2)
        
        # Add a white background behind the logo for better scannability
        # And ensure it's drawn using the specified dotType if it's a "dot-like" logo
        bg_size = (logo_pil.width + 10, logo_pil.height + 10)
        bg_pos = ((qr_width - bg_size[0]) // 2, (qr_height - bg_size[1]) // 2)
        
        # Create a background area with the specified dotType
        bg_area = Image.new('RGBA', img.size, (255,255,255,0)) # Transparent canvas
        bg_draw = ImageDraw.Draw(bg_area)
        
        # Draw a solid white rectangle/rounded rect for the logo background
        # We can make this area itself have rounded corners for example, matching the dotType if applicable
        if dotType == "rounded" or dotType == "softCornerSquare":
            radius_bg = min(bg_size) // 4
            bg_draw.rounded_rectangle((bg_pos[0], bg_pos[1], bg_pos[0] + bg_size[0], bg_pos[1] + bg_size[1]), 
                                       radius=radius_bg, fill='white')
        else:
            bg_draw.rectangle((bg_pos[0], bg_pos[1], bg_pos[0] + bg_size[0], bg_pos[1] + bg_size[1]), 
                               fill='white')
        
        # Paste the background area onto the main QR image
        img.paste(bg_area, (0,0), bg_area) # Use bg_area as mask for transparency
        
        # Paste the actual logo on top
        if logo_pil.mode == 'RGBA':
            img.paste(logo_pil, logo_pos, logo_pil)
        else:
            img.paste(logo_pil, logo_pos)
    
    return img

# --- Main generation orchestrator (no changes) ---
def generate_qr_code(
    qr_data: str,
    shape_url: Optional[str] = None,
    logo_url: Optional[str] = None,
    dotType: Optional[str] = None
) -> Image.Image:
    """
    Orchestrates the QR code generation process, handling optional shape, logo, and dotType.
    """
    logo_img = None
    if logo_url:
        logo_img = _download_image(logo_url)

    if shape_url:
        silhouette_img = _download_image(shape_url)
        return create_shaped_qr(
            silhouette_pil=silhouette_img, 
            qr_data=qr_data, 
            logo_pil=logo_img,
            dotType=dotType
        )
    else:
        return create_standard_qr(
            qr_data=qr_data, 
            logo_pil=logo_img,
            dotType=dotType
        )