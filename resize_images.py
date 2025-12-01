# resize_images.py
from PIL import Image
import os

# Target size for 6x9 inch print at 300 DPI
TARGET_WIDTH = 1800   # 6 inches * 300 DPI
TARGET_HEIGHT = 2700  # 9 inches * 300 DPI
DPI = 300

def resize_image(input_path, output_path):
    """Resize an image to 6x9 inches at 300 DPI for printing."""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate aspect ratios
            original_ratio = img.width / img.height
            target_ratio = TARGET_WIDTH / TARGET_HEIGHT
            
            # Resize to cover the target area, then crop to exact size
            if original_ratio > target_ratio:
                # Image is wider, fit by height
                new_height = TARGET_HEIGHT
                new_width = int(new_height * original_ratio)
            else:
                # Image is taller, fit by width
                new_width = TARGET_WIDTH
                new_height = int(new_width / original_ratio)
            
            # Resize with high-quality resampling
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Crop to exact target size (center crop)
            left = (new_width - TARGET_WIDTH) // 2
            top = (new_height - TARGET_HEIGHT) // 2
            right = left + TARGET_WIDTH
            bottom = top + TARGET_HEIGHT
            
            img_cropped = img_resized.crop((left, top, right, bottom))
            
            # Save with 300 DPI metadata
            img_cropped.save(output_path, 'PNG', dpi=(DPI, DPI))
            print(f"  ✅ Resized: {os.path.basename(output_path)}")
            return True
            
    except Exception as e:
        print(f"  ❌ Error processing {input_path}: {e}")
        return False

def main():
    input_dir = "images"
    output_dir = "images_print"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all PNG images
    images = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])
    
    if not images:
        print("❌ No images found in 'images' folder")
        return
    
    print(f"\nResizing {len(images)} images to 6x9 inches at {DPI} DPI")
    print(f"Target resolution: {TARGET_WIDTH}x{TARGET_HEIGHT} pixels")
    print("=" * 60)
    
    success_count = 0
    for image_file in images:
        input_path = os.path.join(input_dir, image_file)
        output_path = os.path.join(output_dir, image_file)
        
        print(f"Processing: {image_file}...")
        if resize_image(input_path, output_path):
            success_count += 1
    
    print("=" * 60)
    print(f"✅ Resized {success_count}/{len(images)} images")
    print(f"📁 Output saved to: {output_dir}/")

if __name__ == "__main__":
    main()
