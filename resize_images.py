# resize_images.py
from PIL import Image, ImageEnhance, ImageFilter
import os

# Print quality DPI
DPI = 300
# Scale factor: multiply original dimensions by this to get print-ready size
# e.g., 600x900 image becomes 1800x2700 (3x scale)
SCALE_FACTOR = 3


def resize_image(input_path, output_path=None):
    """Resize an image to print quality at 300 DPI with quality preservation.
    Scales the image proportionally based on its original dimensions.
    """
    if output_path is None:
        output_path = input_path  # Overwrite original
    
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate target dimensions based on original image size
            target_width = img.width * SCALE_FACTOR
            target_height = img.height * SCALE_FACTOR
            
            # Single-step resize with LANCZOS (highest quality)
            img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Apply subtle sharpening to restore any lost detail from resizing
            img_sharpened = img_resized.filter(
                ImageFilter.UnsharpMask(radius=1.5, percent=80, threshold=2)
            )
            
            # Slightly enhance contrast to make colors pop in print
            enhancer = ImageEnhance.Contrast(img_sharpened)
            img_enhanced = enhancer.enhance(1.05)  # 5% contrast boost
            
            # Save as high-quality PNG with 300 DPI metadata
            img_enhanced.save(
                output_path, 
                'PNG', 
                dpi=(DPI, DPI),
                optimize=True
            )
            print(f"    🔍 Resized ({target_width}x{target_height}): {os.path.basename(output_path)}")
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
    
    print(f"\nResizing {len(images)} images at 300 DPI")
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
