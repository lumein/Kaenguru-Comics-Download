import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from bs4 import BeautifulSoup
import requests
import re
from tkinter import Tk, filedialog, simpledialog
from PIL import Image

def download_image(url, session):
    """Download an image and return its content"""
    response = session.get(url, stream=True)
    response.raw.decode_content = True
    return response.raw.read()

# Create a Tkinter root window (it will not be shown)
root = Tk()
root.withdraw()

# Open a file chooser dialog to select the path
folder_path = Path(filedialog.askdirectory(title="Select the path where you want to create the 'K-Comics' folder"))

# Create a folder named "K-Comics" if it doesn't exist
folder_path = folder_path / "K-Comics"
folder_path.mkdir(exist_ok=True)

# Set the number of comic strips published on zeit.de
count = 627

# Create a session object to reuse the underlying TCP connection
session = requests.Session()

# Create a list to store the image data
images = []

# Iterate over the page numbers (1-13)
for page in range(1, 14):
    # Construct the URL for the current page
    main_url = f'https://www.zeit.de/serie/die-kaenguru-comics?p={page}'

    # Send a GET request to the main page and parse the HTML content
    response = session.get(main_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links to the comic strip pages
    comic_links = soup.find_all('a', class_='zon-teaser-standard__faux-link')

    # Extract the URLs of the comic strip pages
    comic_urls = [link['href'] for link in comic_links]

    # Iterate over the URLs of the comic strip pages
    for url in comic_urls:
        # Send a GET request to the comic strip page and parse the HTML content
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all image tags on the page
        images_tags = soup.find_all('img')

        # Create a regular expression to match the URLs of the comic images
        pattern = re.compile(r'^https://img\.zeit\.de/administratives/kaenguru-comics/\d{4}-\d{2}/\d{2}')

        # Extract the URLs of the comic images that match the pattern
        image_urls = [img['src'] for img in images_tags if 'src' in img.attrs and pattern.match(img['src'])]

        # Create a ThreadPoolExecutor to download images concurrently
        with ThreadPoolExecutor() as executor:
            # Submit tasks to download images and store the future objects in a list
            futures = [executor.submit(download_image, url, session) for url in image_urls]

            # Iterate over the completed tasks
            for future in as_completed(futures):
                # Get the downloaded image data from the future object
                img_data = future.result()

                # Add the image data to the list if it was downloaded successfully
                if img_data is not None:
                    images.append(img_data)

# Convert the image data to PIL Image objects and convert them to RGB mode (required for PDF conversion)
images = [Image.open(io.BytesIO(img_data)).convert("RGB") for img_data in images]

# Set an appropriate name for the final PDF file (e.g., "K-Comics.pdf")
pdf_name = "K-Comics"

# Save all images as a single PDF file in reverse order (to match the original code)
images[0].save(folder_path / f"{pdf_name}.pdf", save_all=True, append_images=images[1:][::-1])

# Save each image as an individual file with decreasing numbers starting from 627 (to match your requirement)
for i, img_data in enumerate(reversed(images), start=1):
    with open(folder_path / f"{count}.jpg", "wb") as f:
        f.write(img_data)
    count -= 1
