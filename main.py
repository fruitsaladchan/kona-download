import requests
from bs4 import BeautifulSoup
import os
import random

def download_image(url, folder):
    response = requests.get(url)
    if response.status_code == 200:
        filename = os.path.join(folder, url.split('/')[-1])
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {url}")

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def rename_images(folder):
    for filename in os.listdir(folder):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            new_name = f"{random.randint(1000000, 9999999)}.jpg"
            os.rename(os.path.join(folder, filename), os.path.join(folder, new_name))
            print(f"Renamed {filename} to {new_name}")

def get_images(tag, character, pages, folder_name):
    base_url = "https://konachan.com/post"
    folder = create_folder(folder_name)

    for page in pages:
        params = {
            'tags': tag + (' ' + character if character else ''),
            'page': page
        }
        
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            images = soup.find_all('a', class_='directlink largeimg')
            for img in images:
                download_image(img['href'], folder)
        else:
            print(f"Failed to retrieve page {page}.")
    
    rename_images(folder)
    print("All images have been renamed.")

def main():
    tag = input("Enter tags (optional): ").strip()
    character = input("Enter characters (optional): ").strip()
    
    if not tag and not character:
        print("You must enter at least one tag or character.")
        return
    
    pages = input("Enter page numbers (space-separated): ").strip().split()
    folder_name = input("Enter folder name: ").strip()
    
    if not folder_name:
        folder_name = "konachan_images"
    
    folder_name = os.path.join(os.getcwd(), folder_name)
    
    get_images(tag, character, pages, folder_name)

if __name__ == "__main__":
    main()

