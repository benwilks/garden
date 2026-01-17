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

### 2. Scrape Seed Data

Run the scraper to extract product URLs from your order history and download detailed growing information + images.

```bash
python scripts/scrape_johnnys_seeds.py orders/<your-order-file>.html data/<output-name>.csv [options]
```

Options:
- `--overwrite`: Overwrite existing data for URLs that have already been scraped. (Default: Skip existing)
- `--limit N`: Scrape only N items (useful for testing).

Example:
```bash
python scripts/scrape_johnnys_seeds.py orders/2025-12_order-history.html data/2026-garden-seeds.csv
```

### 3. Generate Garden Website

Generate the scheduling and guide HTML files using the scraped data.

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
