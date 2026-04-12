import sys
from PIL import Image

def crop_transparent(image_path, output_path):
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Get the bounding box of the non-transparent alpha channel
    bbox = img.getbbox()
    if bbox:
        # Crop the image to the bounding box
        img = img.crop(bbox)
        # Check if the user wants it to be square, add padding to make it square if needed
        # Windows taskbar icons are usually square.
        width, height = img.size
        size = max(width, height)
        # Create a new transparent image of the square size
        new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        # Paste the cropped image into the center
        new_img.paste(img, ((size - width) // 2, (size - height) // 2))
        
        # Save as PNG
        new_img.save(output_path, 'PNG')
        
        # Also save as ICO for electron builder
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        new_img.save(output_path.replace('.png', '.ico'), format='ICO', sizes=icon_sizes)
        print("Success! Saved to", output_path)
    else:
        print("Image is entirely transparent or empty")

crop_transparent('frontend/public/logo2.png', 'frontend/public/logo2_cropped.png')
