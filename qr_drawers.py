# qr_drawers.py

from PIL import Image, ImageDraw
from typing import List
import math

def _is_finder_pattern_module(row_idx: int, col_idx: int, num_modules: int, border: int) -> bool:
    """
    Checks if a given module coordinate (after accounting for border)
    falls within a finder pattern.
    """
    r = row_idx - border
    c = col_idx - border
    data_num_modules = num_modules - (2 * border)
    finder_size = 7
    
    # Top-left corner
    if (0 <= r < finder_size and 0 <= c < finder_size):
        return True
    # Top-right corner
    if (0 <= r < finder_size and data_num_modules - finder_size <= c < data_num_modules):
        return True
    # Bottom-left corner
    if (data_num_modules - finder_size <= r < data_num_modules and 0 <= c < finder_size):
        return True
    
    return False

def draw_module(draw: ImageDraw.ImageDraw, box: tuple, dotType: str, color: str = "black", is_finder: bool = False):
    """
    Draws a single QR code module (dot) on the image canvas based on the specified style.
    If is_finder is True, it always draws a plain square regardless of dotType.
    """
    x1, y1, x2, y2 = box

    if is_finder:
        draw.rectangle(box, fill=color)
        return

    w, h = x2 - x1, y2 - y1

    if dotType == "heart":
        draw.ellipse((x1, y1, x1 + w/2, y1 + h/2), fill=color)
        draw.ellipse((x1 + w/2, y1, x2, y1 + h/2), fill=color)
        draw.polygon([(x1, y1 + h/4), (x2, y1 + h/4), (x1 + w/2, y2)], fill=color)

    elif dotType == "star":
        center_x, center_y = x1 + w / 2, y1 + h / 2
        outer_radius = min(w, h) / 2
        inner_radius = outer_radius * 0.4
        
        points = []
        for i in range(5):
            angle = math.radians(-90 + i * 72)
            points.append((
                center_x + outer_radius * math.cos(angle),
                center_y + outer_radius * math.sin(angle)
            ))
            angle = math.radians(-90 + 36 + i * 72)
            points.append((
                center_x + inner_radius * math.cos(angle),
                center_y + inner_radius * math.sin(angle)
            ))
        draw.polygon(points, fill=color)

    elif dotType == "club":
        r = w * 0.28
        cx = x1 + w/2
        draw.ellipse((cx - r, y1 + h*0.05, cx + r, y1 + h*0.05 + 2*r), fill=color)
        draw.ellipse((x1 + w*0.05, y1 + h*0.3, x1 + w*0.05 + 2*r, y1 + h*0.3 + 2*r), fill=color)
        draw.ellipse((x2 - w*0.05 - 2*r, y1 + h*0.3, x2 - w*0.05, y1 + h*0.3 + 2*r), fill=color)
        draw.polygon([(cx, y1 + h*0.5), (x1 + w*0.3, y2), (x2 - w*0.3, y2)], fill=color)

    elif dotType == "spade":
        head_h = h * 0.7
        draw.ellipse((x1, y1 + head_h/2, x1 + w/2, y1 + head_h), fill=color)
        draw.ellipse((x1 + w/2, y1 + head_h/2, x2, y1 + head_h), fill=color)
        draw.polygon([(x1, y1 + head_h*0.75), (x2, y1 + head_h*0.75), (x1 + w/2, y1)], fill=color)
        draw.polygon([(x1 + w/2, y1 + head_h*0.8), (x1 + w*0.35, y2), (x2 - w*0.35, y2)], fill=color)
    
    elif dotType == "rounded":
        radius = (x2 - x1) // 2
        draw.rounded_rectangle(box, radius=radius, fill=color)
        
    elif dotType == "softCornerSquare":
        radius = (x2 - x1) // 4
        draw.rounded_rectangle(box, radius=radius, fill=color)
        
    elif dotType == "dot":
        inset = (x2 - x1) * 0.15
        draw.ellipse((x1 + inset, y1 + inset, x2 - inset, y2 - inset), fill=color)

    elif dotType == "diamond":
        mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
        points = [(mid_x, y1), (x2, mid_y), (mid_x, y2), (x1, mid_y)]
        draw.polygon(points, fill=color)
        
    elif dotType == "verticalBar":
        width = (x2 - x1) // 2
        offset = (x2 - x1 - width) // 2
        draw.rectangle([x1 + offset, y1, x1 + offset + width, y2], fill=color)
        
    elif dotType == "horizontalBar":
        height = (y2 - y1) // 2
        offset = (y2 - y1 - height) // 2
        draw.rectangle([x1, y1 + offset, x2, y1 + offset + height], fill=color)

    else:  # Default to "square"
        draw.rectangle(box, fill=color)

# --- MODIFIED FUNCTION ---
def draw_qr_from_matrix(qr_matrix: List[List[bool]], border: int, dotType: str, size: int):
    """
    Creates a complete PIL Image of a QR code from a matrix using a specified dot style,
    while preserving finder patterns as squares.
    """
    # The qr_matrix from the library already includes the border.
    # Its length is the total number of modules across one side.
    num_modules = len(qr_matrix)
    
    # Calculate module size based on the final desired image size and total modules.
    module_size = size // num_modules
    # The size of the canvas before the final resize for anti-aliasing.
    img_size = num_modules * module_size
    
    img = Image.new("RGBA", (img_size, img_size), "white")
    draw = ImageDraw.Draw(img)
    
    # 'r' and 'c' are the absolute row and column indices in the full QR matrix.
    for r, row in enumerate(qr_matrix):
        for c, cell in enumerate(row):
            if cell:
                # Calculate the top-left corner of the module box using absolute coordinates.
                x1 = c * module_size
                y1 = r * module_size
                box = (x1, y1, x1 + module_size, y1 + module_size)
                
                # Your existing _is_finder_pattern_module works correctly when given
                # the absolute coordinates (r, c), the total size (num_modules), and the border.
                is_finder = _is_finder_pattern_module(r, c, num_modules, border)
                
                draw_module(draw, box, dotType, is_finder=is_finder)
                
    # Resize to the exact requested size for better anti-aliasing.
    return img.resize((size, size), Image.Resampling.LANCZOS)