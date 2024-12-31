import os
import requests
from bs4 import BeautifulSoup
import random
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import mimetypes
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def slowprint(text, delay=1./400):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print("")

def setup_requests_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def is_valid_image(content):
    """Validate if the content is actually an image"""
    image_formats = ['image/jpeg', 'image/png', 'image/gif']
    content_type = mimetypes.guess_type(content)[0]
    return content_type in image_formats

def download_image(url, folder, session, pbar):
    """Download image with retry mechanism and validation"""
    try:
        response = session.get(url, timeout=10, stream=True)
        if response.status_code == 200:
            # Check file size (skip if larger than 50MB)
            content_length = int(response.headers.get('content-length', 0))
            if content_length > 50 * 1024 * 1024:  # 50MB
                logger.warning(f"Skipping {url} - File too large ({content_length/1024/1024:.2f}MB)")
                return False

            filename = os.path.join(folder, url.split('/')[-1])
            
            # Validate content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Skipping {url} - Not an image (content-type: {content_type})")
                return False

            # Download with progress
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def rename_images(folder):
    # Get list of image files first
    image_files = [f for f in os.listdir(folder) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    # Use tqdm for renaming progress
    for filename in tqdm(image_files, desc="Renaming images"):
        new_name = f"{random.randint(1000000, 9999999)}.jpg"
        os.rename(os.path.join(folder, filename), os.path.join(folder, new_name))

def parse_pages(pages_input):
    pages = set()  
    for part in pages_input.split():
        if '-' in part:  
            start, end = map(int, part.split('-'))
            pages.update(range(start, end + 1))  
        else:
            pages.add(int(part))  
    return sorted(pages)  

def get_images(tag, character, pages, folder_name, nsfw, max_workers=5):
    base_url = "https://konachan.com/post?tags=" if nsfw else "https://konachan.net/post?tags="
    folder = create_folder(folder_name)
    session = setup_requests_session()
    
    image_urls = []
    for page in tqdm(pages, desc="Fetching pages"):
        params = {'page': page}
        if tag or character:
            params['tags'] = (tag + ' ' + character).strip()
        
        try:
            response = session.get(base_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            images = soup.find_all('a', class_='directlink largeimg')
            image_urls.extend([img['href'] for img in images])
            
            # Add rate limiting
            time.sleep(1)  # Be nice to the server
        except Exception as e:
            logger.error(f"Error fetching page {page}: {str(e)}")
    
    if not image_urls:
        logger.warning("No images found!")
        return

    # Download images concurrently
    successful_downloads = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        # Create progress bars for each image
        progress_bars = []
        for url in image_urls:
            # Get file size first
            try:
                response = session.head(url)
                file_size = int(response.headers.get('content-length', 0))
            except:
                file_size = 0
            
            # Get filename and truncate if too long
            filename = url.split('/')[-1]
            if len(filename) > 20:
                filename = filename[:17] + "..."
            
            pbar = tqdm(
                total=file_size,
                desc=f"[{len(progress_bars) + 1}/{len(image_urls)}] {filename}",
                unit='B',
                unit_scale=True,
                leave=True,
                ncols=80  # Fixed width for cleaner display
            )
            progress_bars.append(pbar)
            futures.append(executor.submit(download_image, url, folder, session, pbar))
        
        # Wait for all downloads to complete
        for future, pbar in zip(futures, progress_bars):
            if future.result():
                successful_downloads += 1
            pbar.close()

        print("\n")  # Add some spacing after all progress bars
        logger.info(f"Successfully downloaded {successful_downloads} out of {len(image_urls)} images")

    rename_images(folder)
    slowprint("\nAll images downloaded successfully!")
    slowprint("\033[1;36m ==============================================")

def main():
    try:
        os.system("figlet Kona Downloader")
        slowprint("\033[1;36m ==============================================")
        print(" ")
        
        tag = input("Enter tags (eg long_hair, skirt, original, touhou. etc): ").strip()
        character = input("Enter characters (eg hatsune_miku, kagamine_rin, yakumo_yukari etc): ").strip()

        while True:
            try:
                pages_input = input("Enter pages (eg. 1 3 5 or 1-5 | default is 1 page): ").strip()
                if not pages_input:
                    pages = [1]
                else:
                    pages = parse_pages(pages_input)
                if pages:
                    break
                print("Invalid page format. Please try again.")
            except ValueError:
                print("Invalid page numbers. Please try again.")

        folder_name = input("Enter folder name (default: images): ").strip() or "images"
        
        while True:
            nsfw_input = input("Do you want NSFW images? (yes/no leave blank for NSFW): ").strip().lower()
            if nsfw_input in ['yes', 'no', '']:
                nsfw = nsfw_input in ['yes', '']
                break
            print("\033[1;91mInvalid input! Please enter 'yes', 'no', or leave blank for NSFW.\033[0m")

        print(" ")
        slowprint("\033[1;36m ==============================================")
        folder_name = os.path.join(os.getcwd(), folder_name)
        
        get_images(tag, character, pages, folder_name, nsfw)

    except KeyboardInterrupt:
        logger.info("\nExiting...")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        sys.exit()

if __name__ == "__main__":
    main()

