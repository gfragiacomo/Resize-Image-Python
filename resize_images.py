import torch
import torchvision.transforms as transforms
import os
import tkinter as tk
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from torch.utils.data import Dataset, DataLoader

class ImageFolder(Dataset):
   def __init__(self, input_dir, max_size=1920):
       self.image_paths = []
       self.output_paths = []
       self.icc_profiles = []
       self.max_size = max_size
       self._scan_dir(input_dir)
       
   def _scan_dir(self, input_dir):
       for root, _, files in os.walk(input_dir):
           for f in files:
               if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                   self.image_paths.append(os.path.join(root, f))
                   
   def __len__(self):
       return len(self.image_paths)
       
   def __getitem__(self, idx):
       img_path = self.image_paths[idx]
       with Image.open(img_path) as img:
           icc_profile = img.info.get('icc_profile')
           if img.mode in ('RGBA', 'P'):
               img = img.convert('RGB')
           return transforms.ToTensor()(img), icc_profile, img_path

def process_batch(batch, device, max_size=1920):
   images, icc_profiles, paths = batch
   images = images.to(device)
   
   batch_size, _, h, w = images.shape
   ratio = max_size / max(h, w)
   
   if ratio < 1:
       new_h = int(h * ratio)
       new_w = int(w * ratio)
       resize = transforms.Resize((new_h, new_w), antialias=True)
       images = resize(images)
   
   return images.cpu(), icc_profiles, paths

def save_images(images, icc_profiles, input_paths, output_dir):
   to_pil = transforms.ToPILImage()
   for img, icc, in_path in zip(images, icc_profiles, input_paths):
       rel_path = os.path.relpath(os.path.dirname(in_path), os.path.dirname(in_path))
       output_subdir = os.path.join(output_dir, rel_path)
       os.makedirs(output_subdir, exist_ok=True)
       
       output_path = os.path.join(
           output_subdir, 
           os.path.splitext(os.path.basename(in_path))[0] + '.jpg'
       )
       
       img_pil = to_pil(img)
       if icc:
           img_pil.save(output_path, 'JPEG', quality=60, optimize=True, icc_profile=icc)
       else:
           img_pil.save(output_path, 'JPEG', quality=60, optimize=True)

def main():
   device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
   print(f"Using: {device}")
   
   root = tk.Tk()
   root.withdraw()
   input_dir = filedialog.askdirectory(title="Select Input Folder")
   if not input_dir:
       return
       
   output_dir = filedialog.askdirectory(title="Select Output Folder")
   if not output_dir:
       return

   dataset = ImageFolder(input_dir)
   dataloader = DataLoader(
       dataset, 
       batch_size=4,
       num_workers=os.cpu_count(),
       pin_memory=True if torch.cuda.is_available() else False
   )
   
   processed = 0
   for batch in dataloader:
       processed_images, profiles, paths = process_batch(batch, device)
       save_images(processed_images, profiles, paths, output_dir)
       processed += len(paths)
       print(f"Processed: {processed}")
   
   print("Complete!")

if __name__ == "__main__":
   main()