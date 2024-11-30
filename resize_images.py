from PIL import Image
from io import BytesIO
import os
import tkinter as tk
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor
from PIL import ImageCms
from PIL.ImageCms import Intent

def select_folder(title):
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)

def convert_to_srgb(img):
    try:
        if 'icc_profile' in img.info:
            input_profile = ImageCms.ImageCmsProfile(BytesIO(img.info['icc_profile']))
            output_profile = ImageCms.createProfile('sRGB')
            transform = ImageCms.buildTransformFromOpenProfiles(
                input_profile, output_profile, 
                img.mode, img.mode, 
                renderingIntent=Intent.RELATIVE_COLORIMETRIC
            )
            img = ImageCms.applyTransform(img, transform)
    except Exception as e:
        print(f"Color profile conversion warning: {e}")
    return img

def process_image(input_path, output_path, max_size=1350):
    try:
        with Image.open(input_path) as img:
            exif = img.info.get('exif')
            
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Convert color profile to sRGB
            img = convert_to_srgb(img)
            
            ratio = max_size / max(img.size)
            if ratio < 1:
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            save_args = {
                'quality': 85, 
                'optimize': True
            }
            if exif:
                save_args['exif'] = exif
                
            img.save(output_path, 'JPEG', **save_args)
            return "processed"
            
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return "error"


def main():
    input_dir = select_folder("Select Input Folder")
    if not input_dir:
        return
        
    output_dir = select_folder("Select Output Folder")
    if not output_dir:
        return
    
    tasks = []
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                input_path = os.path.join(root, filename)
                rel_path = os.path.relpath(root, input_dir)
                output_subdir = os.path.join(output_dir, rel_path)
                output_filename = os.path.splitext(filename)[0] + '.jpg'
                output_path = os.path.join(output_subdir, output_filename)
                tasks.append((input_path, output_path))

    processed = 0
    errors = 0
    
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        for result in executor.map(lambda x: process_image(*x), tasks):
            if result == "processed":
                processed += 1
                print(f"Processed: {processed}")
            else:
                errors += 1

    print(f"\nComplete! Processed: {processed}, Errors: {errors}")

if __name__ == "__main__":
    main()