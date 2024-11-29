from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def select_folder(title):
    """
    Opens a folder selection dialog
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    folder = filedialog.askdirectory(title=title)
    return folder if folder else None

def resize_images(input_dir, output_dir, max_size=1920):
    """
    Resize all images in input_dir and its subdirectories
    max_size: the length of the longest edge
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Supported image formats
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    
    # Counter for processed images
    processed = 0
    errors = 0
    
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            if filename.lower().endswith(image_extensions):
                input_path = os.path.join(root, filename)
                
                # Create relative path for output
                rel_path = os.path.relpath(root, input_dir)
                output_subdir = os.path.join(output_dir, rel_path)
                
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                
                # Always save as JPG
                output_filename = os.path.splitext(filename)[0] + '.jpg'
                output_path = os.path.join(output_subdir, output_filename)
                
                try:
                    with Image.open(input_path) as img:
                        # Store the ICC profile
                        icc_profile = img.info.get('icc_profile')
                        
                        # Convert image to RGB if it's not
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        
                        # Calculate new dimensions
                        ratio = max_size / max(img.size)
                        if ratio < 1:  # Only resize if image is larger than max_size
                            new_size = tuple(int(dim * ratio) for dim in img.size)
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                        
                        # Save the resized image with 40% quality and original ICC profile
                        if icc_profile:
                            img.save(output_path, 'JPEG', quality=40, optimize=True, 
                                   icc_profile=icc_profile)
                        else:
                            img.save(output_path, 'JPEG', quality=40, optimize=True)
                            
                        processed += 1
                        print(f"Processed ({processed}): {input_path} -> {output_path}")
                except Exception as e:
                    print(f"Error processing {input_path}: {e}")
                    errors += 1
    
    return processed, errors

def main():
    print("Image Batch Resizer")
    print("==================")
    print("This script will resize images to have a longest edge of 1920 pixels")
    print("and save them as JPG files with 40% quality while preserving color profiles.")
    print("==================\n")
    
    # Select input folder
    print("Please select the INPUT folder containing your images...")
    input_dir = select_folder("Select Input Folder")
    if not input_dir:
        print("No input folder selected. Exiting...")
        return
    
    # Select output folder
    print("\nPlease select the OUTPUT folder for resized images...")
    output_dir = select_folder("Select Output Folder")
    if not output_dir:
        print("No output folder selected. Exiting...")
        return
    
    # Confirm selections
    print(f"\nInput folder: {input_dir}")
    print(f"Output folder: {output_dir}")
    print("\nProcessing images...")
    
    # Process images
    processed, errors = resize_images(input_dir, output_dir)
    
    # Show completion message
    print("\n==================")
    print(f"Processing complete!")
    print(f"Successfully processed: {processed} images")
    if errors > 0:
        print(f"Errors encountered: {errors} images")
    print("==================")

if __name__ == "__main__":
    main()