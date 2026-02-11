import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
import sys

def extract_urls_from_history(html_path):
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"File {html_path} not found.")

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all product line items
    product_divs = soup.find_all('div', class_='product-line-item-details')

    urls = []
    for div in product_divs:
        # Find the anchor tag within the details div
        link = div.find('a', href=True)
        if link:
            urls.append(link['href'])

    # Remove duplicates (images and titles often both have links)
    unique_urls = list(dict.fromkeys(urls))
    return unique_urls

def create_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def download_image(img_url, product_name, output_dir="site/images"):
    if not img_url:
        return None
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        slug = create_slug(product_name)
        ext = os.path.splitext(img_url)[1]
        if not ext or len(ext) > 5: # Basic check if ext is valid
            ext = ".jpg"
        
        filename = f"{slug}{ext}"
        filepath = os.path.join(output_dir, filename)
        
        # Check if image already exists
        if os.path.exists(filepath):
            return f"images/{filename}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(img_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return f"images/{filename}"
        else:
            print(f"Failed to download image: {img_url}")
            return None
    except Exception as e:
        print(f"Error downloading image for {product_name}: {e}")
        return None

def scrape_johnnys_precise(url):
    try:
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- 1. Product Name ---
        name_tag = soup.find('h1', class_='product-name')
        product_name = name_tag.get_text(" ", strip=True) if name_tag else "Unknown"

        # --- 2. Quick Facts (Fixed Logic) ---
        # We iterate through the Description List (dl)
        quick_facts = {}
        facts_list = soup.find('dl', class_='c-facts__list')
        
        if facts_list:
            terms = facts_list.find_all('dt', class_='c-facts__term')
            defs = facts_list.find_all('dd', class_='c-facts__definition')
            
            for t, d in zip(terms, defs):
                # FIX: Only get the text from the <h3> tag to ignore the 'About' button text
                h3 = t.find('h3')
                if h3:
                    key = h3.get_text(strip=True)
                else:
                    # Fallback if no h3, but strip out the button text if present
                    key = t.get_text(strip=True).split('About')[0]
                
                # Clean the value
                val = d.get_text(" ", strip=True)
                quick_facts[key] = val

        # --- 3. Growing Information (Fixed Logic) ---
        # The data is inside 's-lgc-pdp-content' inside the accordion
        growing_info_text = "N/A"
        
        # Method A: Look for specific class from your file
        growing_div = soup.find('div', class_='s-lgc-pdp-content')
        
        # Method B: Fallback - Look for the header "Growing Information" and grab the next container
        if not growing_div:
            header_link = soup.find('a', string=re.compile(r"Growing Information", re.I))
            if header_link:
                # Go up to the header, then find the next sibling div (the panel body)
                header_div = header_link.find_parent('div', class_='c-accordion__header')
                if header_div:
                    growing_div = header_div.find_next_sibling('div', class_='c-accordion__body')

        if growing_div:
            # Get text, separating headers (SCIENTIFIC NAME:) from values with a pipe |
            growing_info_text = growing_div.get_text(separator=" | ", strip=True)

        # --- 4. Image URL ---
        image_url = None
        # Try Open Graph image first
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image_url = og_image.get("content")
        
        # Fallback to finding img tag if needed, but og:image is usually best for scraping
        if not image_url:
            # Look for main product image
            img_tag = soup.find('img', class_='c-product-image__img')
            if img_tag:
                 image_url = img_tag.get('src')
        
        # Try Schema.org itemprop="image"
        if not image_url:
             img_tag = soup.find('img', itemprop='image')
             if img_tag:
                 image_url = img_tag.get('src')

        if not image_url:
            # Look for main product image with class (Salesforce Commerce Cloud standard)
            img_tag = soup.find('img', class_='c-product-image__img')
            if img_tag:
                 image_url = img_tag.get('src')

        image_path = "N/A"
        if image_url:
            image_path = download_image(image_url, product_name)

        return {
            'Product Name': product_name,
            'Latin Name': quick_facts.get('Latin Name', 'N/A'),
            'Days to Maturity': quick_facts.get('Days To Maturity', 'N/A'),
            'Life Cycle': quick_facts.get('Life Cycle', 'N/A'),
            'Hybrid Status': quick_facts.get('Hybrid Status', 'N/A'),
            'Disease Resistance': quick_facts.get('Disease Resistance Codes', 'N/A'),
            'Growing Info': growing_info_text,
            'URL': url,
            'Image Path': image_path if image_path else "N/A"
        }

    except Exception as e:
        print(f"Error extracting {url}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Scrape Johnny\'s Seeds data from order history.')
    parser.add_argument('input_path', nargs='?', default='orders', help='Path to the order history HTML file or directory (default: orders)')
    parser.add_argument('output_csv', nargs='?', default='data/garden_seeds.csv', help='Path to the output CSV file (default: data/garden_seeds.csv)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing data even if URL is already scraped')
    parser.add_argument('--limit', type=int, help='Limit the number of items to process')
    
    args = parser.parse_args()
    
    # Determine input files
    html_files = []
    if os.path.isdir(args.input_path):
        for root, dirs, files in os.walk(args.input_path):
            for file in files:
                if file.lower().endswith('.html'):
                    html_files.append(os.path.join(root, file))
    elif os.path.isfile(args.input_path):
        html_files.append(args.input_path)
    else:
        print(f"Error: Input path '{args.input_path}' not found.")
        return

    if not html_files:
        print(f"No HTML files found in {args.input_path}")
        return

    print(f"Processing {len(html_files)} order history files...")
    all_urls = set()
    for html_file in html_files:
        print(f"  Reading {html_file}...")
        try:
            file_urls = extract_urls_from_history(html_file)
            all_urls.update(file_urls)
        except Exception as e:
            print(f"  Error reading {html_file}: {e}")

    urls = list(all_urls)
    print(f"Found {len(urls)} unique product URLs across all files.")
    
    # Load existing data to check for duplicates
    existing_urls = set()
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    
    if os.path.exists(args.output_csv):
        try:
            df_existing = pd.read_csv(args.output_csv, encoding='utf-8')
            if 'URL' in df_existing.columns:
                existing_urls = set(df_existing['URL'].tolist())
            print(f"Resuming from {args.output_csv}. {len(existing_urls)} items already scraped.")
        except Exception as e:
            print(f"Warning: Could not read existing CSV: {e}")

    print("Scraping product data...")
    scraped_count = 0
    
    for i, url in enumerate(urls):
        if args.limit and scraped_count >= args.limit:
            print(f"Reached limit of {args.limit} scraped items.")
            break

        if url in existing_urls and not args.overwrite:
            # Silent skip or maybe just log if verbose, but let's keep it clean
            continue

        print(f"[{i+1}/{len(urls)}] Scraping {url}...")
        res = scrape_johnnys_precise(url)
        
        if res:
            print(f"  Found: {res['Product Name']} - DTM: {res['Days to Maturity']}")
            
            # Iterative Save
            df_new = pd.DataFrame([res])
            # Check if header is needed (file doesn't exist or is empty)
            header = not os.path.exists(args.output_csv) or os.stat(args.output_csv).st_size == 0
            df_new.to_csv(args.output_csv, mode='a', header=header, index=False, encoding='utf-8')
            scraped_count += 1
            
            # Add to existing urls so we don't try to scrape it again if there are duplicates in the list somehow
            existing_urls.add(url)
        else:
            print(f"  Failed to scrape {url}")
        
        time.sleep(2) # Respectful delay

    print(f"Scraping complete! Data saved to {args.output_csv}")
    
    # Trigger Site Generation
    print("\nStarting site generation...")
    import subprocess
    try:
        generate_script = os.path.join(os.path.dirname(__file__), 'generate_garden_data.py')
        result = subprocess.run([sys.executable, generate_script, args.output_csv], check=True)
        if result.returncode == 0:
            print("Site generation successful!")
        else:
            print("Site generation failed.")
    except Exception as e:
        print(f"Error running site generation: {e}")

if __name__ == "__main__":
    main()
