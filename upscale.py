import sys
from PIL import Image

def rebuild_ico(image_path, output_path):
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Needs to be exactly 256x256 internally for Electron
    # We will resize the already cropped image to min 256x256 if it's smaller, or just scale it up
    img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img_256.save(output_path, format='ICO', sizes=icon_sizes)
    print("Success! Saved ICO with proper sizes to", output_path)

rebuild_ico('frontend/public/logo2_cropped.png', 'frontend/public/logo2_cropped.ico')
