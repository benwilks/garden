import requests
import sys
import os

def download_image(search_term, output_filename):
    print(f"Searching for '{search_term}'...")
    url = "https://commons.wikimedia.org/w/api.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_term,
        "gsrnamespace": 6,  # File namespace
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
        "gsrlimit": 5  # Get top 5 to check for valid extensions
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            print(f"No images found for {search_term}")
            return

        image_url = None
        for page_id, page in pages.items():
            image_info = page.get("imageinfo", [])
            if not image_info:
                continue
            
            temp_url = image_info[0]["url"]
            ext = temp_url.lower().split('.')[-1]
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                image_url = temp_url
                print(f"Found valid image: {image_url}")
                break
        
        if not image_url:
            print(f"No valid jpg/png images found for {search_term}")
            return

        print(f"Downloading from {image_url}...")
        
        img_response = requests.get(image_url, headers=headers)
        if img_response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(img_response.content)
            print(f"Saved to {output_filename}")
        else:
            print(f"Failed to download image. Status code: {img_response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python download_wiki_images.py <search_term> <output_path>")
        sys.exit(1)
    
    search_term = sys.argv[1]
    output_path = sys.argv[2]
    download_image(search_term, output_path)
