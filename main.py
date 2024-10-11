import os
import requests
from bs4 import BeautifulSoup
import random
import time
import sys

def slowprint(text, delay=1./400):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print("")

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

def parse_pages(pages_input):
    pages = set()  
    for part in pages_input.split():
        if '-' in part:  
            start, end = map(int, part.split('-'))
            pages.update(range(start, end + 1))  
        else:
            pages.add(int(part))  
    return sorted(pages)  

def get_images(tag, character, pages, folder_name, nsfw):
    base_url = "https://konachan.com/post?tags=" if nsfw else "https://konachan.net/post?tags="
    folder = create_folder(folder_name)

    for page in pages:
        params = {'page': page}
        if tag or character:
            params['tags'] = (tag + ' ' + character).strip()

        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            images = soup.find_all('a', class_='directlink largeimg')
            for img in images:
                download_image(img['href'], folder)
        else:
            print(f"Failed to retrieve page {page}.")
    
    rename_images(folder)
    print(" ")
    slowprint("All images have been Downloaded.")
    slowprint("Cleaning up...")
    print(" ")
    slowprint("\033[1;36m ==============================================")
    sys.exit()

def main():
    try:
        os.system("figlet Kona Downloader")
        slowprint("\033[1;36m ==============================================")
        print(" ")
        tag = input("Enter tags (eg long_hair, skirt, original, touhou. etc): ").strip()
        character = input("Enter characters (eg hatsune_miku, kagamine_rin, yakumo_yukari etc): ").strip()

        pages_input = input("Enter pages (eg. 1 3 5 or 1-5 | default is 1 page): ").strip()
        if not pages_input:
            pages = [1]  # Default to page 1 if no input
        else:
            pages = parse_pages(pages_input)

        folder_name = input("Enter folder name: ").strip()
        if not folder_name:
            folder_name = "images"
        
        while True:
            nsfw_input = input("Do you want NSFW images? (yes/no leave blank for NSFW): ").strip().lower()
            if nsfw_input in ['yes', 'no', '']:
                nsfw = nsfw_input in ['yes', '']
                break
            else:
                print("\033[1;91mInvalid input! Please enter 'yes', 'no', or leave blank for NSFW.\033[0m")

        print(" ")
        slowprint("\033[1;36m ==============================================")
        folder_name = os.path.join(os.getcwd(), folder_name)
        
        get_images(tag, character, pages, folder_name, nsfw)

    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    main()

