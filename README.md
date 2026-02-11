# Garden Planner & Seed Scraper

This project helps you organize your garden schedule by scraping seed data from Johnny's Selected Seeds order history and generating a personalized planting calendar and growing guide website.

## Directory Structure

- `orders/`: Place your Johnny's Seeds order history HTML files here.
- `data/`: Stores the scraped seed data (CSV) and generated schedule data (JSON).
- `site/`: The generated static website (schedule, guides, plant details).
- `scripts/`: Python scripts for scraping and site generation.

## Setup

Ensure you have Python installed along with the required packages:

```bash
pip install pandas beautifulsoup4 requests
```

## Usage

### 1. Download Order History

1. Log in to your [Johnny's Selected Seeds](https://www.johnnyseeds.com/) account.
2. Navigate to your Order History.
3. Open a specific order details page.
4. Save the page as HTML (Right-click -> Save As -> Webpage, Complete/HTML Only) into the `orders/` directory. 
   - Example: `orders/2025-12_order-history.html`

### 2. Scrape Seed Data & Generate Site

Run the scraper to extract product URLs from your order history files and download detailed growing information + images. This will automatically process all `.html` files in the specified directory (default: `orders/`), scrape any new items, and then generate the website.

```bash
python scripts/scrape_johnnys_seeds.py [input_path] [output_csv] [options]
```

Arguments:
- `input_path`: Path to an individual HTML file or a directory containing HTML files. (Default: `orders/`)
- `output_csv`: Path to the output CSV file. New data will be appended. (Default: `data/garden_seeds.csv`)

Options:
- `--overwrite`: Overwrite existing data for URLs that have already been scraped. (Default: Skip existing)
- `--limit N`: Scrape only N items (useful for testing).

**Example (Process all orders and append to existing 2026 data):**
```bash
python scripts/scrape_johnnys_seeds.py orders/ data/2026-garden-seeds.csv
```

**Example (Default behavior):**
```bash
python scripts/scrape_johnnys_seeds.py
```

### 3. (Optional) Manually Generate Garden Website

The scraper automatically triggers site generation, but you can also run it manually if needed:

```bash
python scripts/generate_garden_data.py data/<output-name>.csv
```

Example:
```bash
python scripts/generate_garden_data.py data/2026-garden-seeds.csv
```

**Note:** The script detects transplanting instructions in the growing info. Even for crops typically direct sown (like Lettuce or Cucumber), if the vendor provides transplanting details (e.g., "Sow indoors 3-4 weeks before..."), the schedule will calculate and display the indoor start dates and transplant window.

If no argument is provided, it defaults to using `data/johnnys_data_fixed.csv`.

### 4. View the Site

Open `site/schedule.html` in your web browser to view your personalized planting schedule and growing guides.
