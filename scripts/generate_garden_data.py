import pandas as pd
import re
import datetime
import json
import os
import html
import argparse
import sys

# --- CONFIGURATION ---
LFD = datetime.date(2026, 5, 10)  # Last Frost Date
FFD = datetime.date(2026, 11, 5)  # First Frost Date
OUTPUT_DIR = "site/plants"
SCHEDULE_JSON = "data/schedule_data.json"
SCHEDULE_HTML = "site/schedule.html"

# Default offsets (days relative to LFD) and indoor weeks range
CROP_DEFAULTS = {
    "Tomato":   {"offset": 0, "type": "Transplant", "weeks_indoor_min": 6, "weeks_indoor_max": 8},
    "Pepper":   {"offset": 7, "type": "Transplant", "weeks_indoor_min": 8, "weeks_indoor_max": 10},
    "Eggplant": {"offset": 7, "type": "Transplant", "weeks_indoor_min": 8, "weeks_indoor_max": 10},
    "Cucumber": {"offset": 10, "type": "Direct Sow", "weeks_indoor_min": 3, "weeks_indoor_max": 4},
    "Squash":   {"offset": 10, "type": "Direct Sow", "weeks_indoor_min": 3, "weeks_indoor_max": 4},
    "Zucchini": {"offset": 10, "type": "Direct Sow", "weeks_indoor_min": 3, "weeks_indoor_max": 4},
    "Basil":    {"offset": 10, "type": "Transplant", "weeks_indoor_min": 4, "weeks_indoor_max": 6},
    "Lettuce":  {"offset": -28, "type": "Direct Sow", "weeks_indoor_min": 4, "weeks_indoor_max": 6},
    "Kale":     {"offset": -28, "type": "Direct Sow", "weeks_indoor_min": 4, "weeks_indoor_max": 6},
    "Spinach":  {"offset": -35, "type": "Direct Sow", "weeks_indoor_min": 4, "weeks_indoor_max": 5},
    "Pea":      {"offset": -42, "type": "Direct Sow", "weeks_indoor_min": 0, "weeks_indoor_max": 0},
    "Bean":     {"offset": 10, "type": "Direct Sow", "weeks_indoor_min": 0, "weeks_indoor_max": 0},
    "Carrot":   {"offset": -14, "type": "Direct Sow", "weeks_indoor_min": 0, "weeks_indoor_max": 0},
    "Radish":   {"offset": -28, "type": "Direct Sow", "weeks_indoor_min": 0, "weeks_indoor_max": 0},
    "Turnip":   {"offset": -21, "type": "Direct Sow", "weeks_indoor_min": 0, "weeks_indoor_max": 0},
    "Onion":    {"offset": -28, "type": "Transplant", "weeks_indoor_min": 10, "weeks_indoor_max": 12},
    "Leek":     {"offset": -28, "type": "Transplant", "weeks_indoor_min": 10, "weeks_indoor_max": 12},
    "Flower":   {"offset": 7, "type": "Transplant", "weeks_indoor_min": 4, "weeks_indoor_max": 6},
    "Herb":     {"offset": 0, "type": "Transplant", "weeks_indoor_min": 6, "weeks_indoor_max": 8},
}

SCHEDULE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Somerville Garden Schedule 2026</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 2rem; background: #f5f5f5; }
        h1 { color: #2c3e50; }
        .controls { margin-bottom: 1rem; }
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; cursor: pointer; user-select: none; }
        th:hover { background-color: #45a049; }
        tr:hover { background-color: #f1f1f1; }
        .method-indoor { color: #d35400; font-weight: bold; }
        .method-direct { color: #27ae60; font-weight: bold; }
        .date-cell { font-variant-numeric: tabular-nums; white-space: nowrap; }
        input[type="text"] { padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 200px; }
        .links { margin-bottom: 20px; }
        a { color: #2980b9; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>

    <div class="links">
        <a href="garden_guide.html">Back to Garden Guide</a>
    </div>

    <h1>Somerville Garden Schedule 2026</h1>
    <p>Last Frost Date: May 10 | First Frost Date: Nov 5</p>

    <div class="controls">
        <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search for crops...">
    </div>

    <table id="scheduleTable">
        <thead>
            <tr>
                <th onclick="sortTable('Crop')">Crop Type &#x2195;</th>
                <th onclick="sortTable('Variety')">Variety &#x2195;</th>
                <th onclick="sortTable('Method')">Method &#x2195;</th>
                <th onclick="sortTable('SortDate')">Start Date (Indoor/Sow) &#x2195;</th>
                <th onclick="sortTable('SortTransplantDate')">Transplant Date &#x2195;</th>
                <th onclick="sortTable('SortDTM')">Days to Maturity &#x2195;</th>
            </tr>
        </thead>
        <tbody id="tableBody">
            <!-- Rows will be populated by JS -->
        </tbody>
    </table>

    <script>
        const gardenData = __DATA_PLACEHOLDER__;
        let currentSort = { key: 'SortDate', asc: true };

        const tableBody = document.getElementById('tableBody');

        function renderTable(data) {
            tableBody.innerHTML = '';
            
            data.forEach(item => {
                const row = document.createElement('tr');
                const methodClass = item.Method === 'Start Indoors' ? 'method-indoor' : 'method-direct';
                
                row.innerHTML = `
                    <td>${item.Crop}</td>
                    <td><a href="${item.Link}">${item.Variety}</a></td>
                    <td class="${methodClass}">${item.Method}</td>
                    <td class="date-cell">${item["Start Range"]}</td>
                    <td class="date-cell">${item["Transplant Range"]}</td>
                    <td>${item.DTM}</td>
                `;
                tableBody.appendChild(row);
            });
        }

        function filterTable() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const filteredData = gardenData.filter(item => 
                item.Crop.toLowerCase().includes(filter) || 
                item.Variety.toLowerCase().includes(filter)
            );
            // Re-apply sort
            sortData(filteredData);
            renderTable(filteredData);
        }

        function sortTable(key) {
            if (currentSort.key === key) {
                currentSort.asc = !currentSort.asc;
            } else {
                currentSort.key = key;
                currentSort.asc = true;
            }
            // Sort full data then filter
            sortData(gardenData);
            filterTable();
        }
        
        function sortData(data) {
            const key = currentSort.key;
            const asc = currentSort.asc ? 1 : -1;
            
            data.sort((a, b) => {
                let valA = a[key];
                let valB = b[key];
                
                // Handle N/A
                if (valA === undefined) valA = "";
                if (valB === undefined) valB = "";
                
                // Case insensitive string sort if string
                if (typeof valA === 'string') valA = valA.toLowerCase();
                if (typeof valB === 'string') valB = valB.toLowerCase();
                
                if (valA < valB) return -1 * asc;
                if (valA > valB) return 1 * asc;
                return 0;
            });
        }

        // Initial Sort and Render
        sortData(gardenData);
        renderTable(gardenData);

    </script>
</body>
</html>
"""

def identify_crop_type(name):
    if not isinstance(name, str):
        return "Other"
    name = name.lower()
    if "tomato" in name: return "Tomato"
    if "pepper" in name or "jalapeno" in name or "habanero" in name: return "Pepper"
    if "eggplant" in name: return "Eggplant"
    if "cucumber" in name: return "Cucumber"
    if "squash" in name or "zucchini" in name: return "Squash"
    if "basil" in name: return "Basil"
    if "lettuce" in name: return "Lettuce"
    if "kale" in name: return "Kale"
    if "spinach" in name: return "Spinach"
    if "pea" in name: return "Pea"
    if "bean" in name: return "Bean"
    if "carrot" in name: return "Carrot"
    if "radish" in name: return "Radish"
    if "turnip" in name: return "Turnip"
    if "onion" in name or "chive" in name: return "Onion"
    if "leek" in name: return "Leek"
    if "dill" in name or "parsley" in name or "cilantro" in name or "thyme" in name or "mint" in name or "sage" in name or "oregano" in name or "lavender" in name or "shiso" in name: return "Herb"
    if "zinnia" in name or "marigold" in name or "sunflower" in name or "nasturtium" in name or "dahlia" in name or "echinacea" in name: return "Flower"
    return "Other"

def parse_growing_info(text):
    info = {
        "full_text": text,
        "culture": "N/A",
        "transplanting": "N/A",
        "pests": "N/A",
        "harvest": "N/A"
    }
    if not isinstance(text, str): 
        info["full_text"] = "No growing info available."
        return info
    
    parts = text.split("|")
    current_key = None
    
    sections = {
        "culture": [],
        "transplanting": [],
        "pests": [],
        "harvest": []
    }

    # Helper to map keys to sections
    def get_section_for_key(k):
        k = k.upper().replace(":", "").strip()
        if "CULTURE" in k: return "culture"
        if "TRANSPLANTING" in k: return "transplanting"
        if "PEST" in k or "DISEASE" in k: return "pests"
        if "HARVEST" in k: return "harvest"
        if "STORAGE" in k: return "harvest" # Append storage to harvest
        if "TRELLIS" in k or "PRUNING" in k: return "culture" # Append to culture
        if "DETERMINATE" in k or "INDETERMINATE" in k: return "culture"
        return None

    for part in parts:
        clean_part = part.strip()
        if not clean_part: continue

        is_key = False
        # Check if this part looks like a key (uppercase, ends with colon)
        if clean_part.endswith(":"):
            section = get_section_for_key(clean_part)
            if section:
                current_key = section
                # If it's a specific subsection header (not the main ones), keep it as bold text
                if clean_part not in ["CULTURE:", "TRANSPLANTING:", "HARVEST:", "INSECT PESTS AND DISEASE:", "DISEASE:", "PESTS:", "INSECT PESTS:"]:
                     sections[current_key].append(f"<strong>{clean_part}</strong>")
                is_key = True
            elif clean_part in ["SCIENTIFIC NAME:", "DAYS TO MATURITY:", "TRANSPLANTS:", "SEEDS/OZ. (AVG.):", "PACKET:"]:
                current_key = None
                is_key = True

        if not is_key and current_key:
            sections[current_key].append(clean_part)

    # Join sections
    for key in sections:
        if sections[key]:
            info[key] = " ".join(sections[key])
        
    return info

def calculate_dates(crop_type, growing_info_text):
    default = CROP_DEFAULTS.get(crop_type, CROP_DEFAULTS["Herb"])
    
    weeks_min = default["weeks_indoor_min"]
    weeks_max = default["weeks_indoor_max"]
    planting_type = default["type"]
    
    # Check text for override, BUT trust defaults for Solanaceae (Tomatoes/Peppers) as user specifically requested earlier starts
    if crop_type not in ["Tomato", "Pepper", "Eggplant"] and isinstance(growing_info_text, str):
        
        # Check for presence of transplanting instructions (excluding "TRANSPLANTS:" which usually refers to yield)
        has_transplant_info = False
        if re.search(r'\bTRANSPLANT(?:ING)?\b.*?:', growing_info_text, re.IGNORECASE):
            has_transplant_info = True

        # Override planting type if explicitly stated
        if "Direct seed (recommended)" in growing_info_text:
            # Only force direct sow if transplanting info is NOT present
            if not has_transplant_info:
                planting_type = "Direct Sow"
                weeks_min = 0
                weeks_max = 0
            else:
                planting_type = "Transplant"
        elif "Transplant (recommended)" in growing_info_text:
            planting_type = "Transplant"
        elif has_transplant_info:
            # If no explicit recommendation but has transplant info, prefer Transplant
            planting_type = "Transplant"
        
        # Look for indoor start weeks: "X-Y weeks before" or "X weeks before"
        match = re.search(r'(\d+)(?:\s*[–-]\s*(\d+))?\s+weeks\s+(?:before|prior)', growing_info_text, re.IGNORECASE)
        if match and planting_type == "Transplant":
            weeks_min = int(match.group(1))
            weeks_max = int(match.group(2)) if match.group(2) else weeks_min
    
    # Calculate Transplant Window (1 week window)
    transplant_start = LFD + datetime.timedelta(days=default["offset"])
    transplant_end = transplant_start + datetime.timedelta(days=7)
    
    # Calculate Indoor Start Window
    if planting_type == "Transplant":
        # Earliest Start = Transplant Start - Max Weeks
        start_early = transplant_start - datetime.timedelta(weeks=weeks_max)
        # Latest Start = Transplant End - Min Weeks
        start_late = transplant_end - datetime.timedelta(weeks=weeks_min)
        
        planting_method = "Start Indoors"
        
        return {
            "method": planting_method,
            "start_range": f"{start_early.strftime('%b %d')} - {start_late.strftime('%b %d')}",
            "transplant_range": f"{transplant_start.strftime('%b %d')} - {transplant_end.strftime('%b %d')}",
            "start_date_obj": start_early, # For sorting
            "transplant_date_obj": transplant_start # For sorting
        }
    else:
        # Direct Sow
        start_early = transplant_start
        start_late = transplant_end
        planting_method = "Direct Sow"
        
        return {
            "method": planting_method,
            "start_range": f"{start_early.strftime('%b %d')} - {start_late.strftime('%b %d')}",
            "transplant_range": "N/A (Direct Sow)",
            "start_date_obj": start_early,
            "transplant_date_obj": transplant_start # Used for direct sow timing too
        }

def create_anchor(name):
    # Create URL friendly anchor
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def main():
    parser = argparse.ArgumentParser(description='Generate garden schedule.')
    parser.add_argument('input_csv', nargs='?', default='data/johnnys_data_fixed.csv', help='Input CSV filename (default: data/johnnys_data_fixed.csv)')
    
    # Also support named argument if preferred, though positional is simpler based on request
    # The user asked: "accept arg for the .csv name". 
    # I'll support both positional and flag for flexibility, but argparse treats positional as required unless nargs='?'
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_csv):
        print(f"Error: File '{args.input_csv}' not found.")
        return

    print(f"Reading data from {args.input_csv}...")
    df = pd.read_csv(args.input_csv)
    
    grouped = {}
    schedule_data = []

    for index, row in df.iterrows():
        name = row['Product Name']
        if not isinstance(name, str):
            continue
            
        crop_type = identify_crop_type(name)
        
        if crop_type not in grouped:
            grouped[crop_type] = []
            
        growing_info = parse_growing_info(row['Growing Info'])
        dates = calculate_dates(crop_type, row['Growing Info'])
        anchor = create_anchor(name)
        
        item = {
            "name": name,
            "anchor": anchor,
            "latin": row['Latin Name'],
            "dtm": row['Days to Maturity'],
            "lifecycle": row['Life Cycle'],
            "hybrid": row['Hybrid Status'],
            "resistance": row['Disease Resistance'],
            "growing_info": growing_info,
            "dates": dates,
            "url": row['URL'],
            "image": row.get('Image Path', 'N/A')
        }
        
        grouped[crop_type].append(item)
        
        # Parse DTM for sorting (extract first number)
        dtm_str = str(row['Days to Maturity'])
        dtm_match = re.search(r'(\d+)', dtm_str)
        sort_dtm = int(dtm_match.group(1)) if dtm_match else 999

        # Handle SortTransplantDate (empty for Direct Sow so they group together)
        sort_transplant_date = ""
        if dates["method"] == "Start Indoors":
             sort_transplant_date = dates["transplant_date_obj"].isoformat()

        schedule_data.append({
            "Crop": crop_type,
            "Variety": name,
            "Link": f"plants/{crop_type.lower()}.html#{anchor}",
            "Method": dates["method"],
            "Start Range": dates["start_range"],
            "Transplant Range": dates["transplant_range"],
            "DTM": row['Days to Maturity'],
            "SortDate": dates["start_date_obj"].isoformat(),
            "SortTransplantDate": sort_transplant_date,
            "SortDTM": sort_dtm
        })

    # Generate HTML Files
    for crop, items in grouped.items():
        filename = f"{OUTPUT_DIR}/{crop.lower()}.html"
        with open(filename, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{crop} Growing Guide</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.6; padding: 0 1rem; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .nav {{ background: #eee; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .variety {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .variety:target {{ border-left: 5px solid #4CAF50; background: #f9fff9; }}
        .meta {{ font-size: 0.9em; color: #666; }}
        .dates {{ background: #e8f5e9; padding: 10px; border-radius: 4px; margin: 10px 0; }}
        .growing-info {{ background: #f9f9f9; padding: 10px; border-radius: 4px; margin-top: 10px; }}
        a {{ color: #2980b9; }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="../schedule.html">Back to Schedule</a> | <a href="../garden_guide.html">Back to Garden Guide</a>
    </div>

    <h1>{crop} Growing Guide</h1>
""")
            
            # General Info from first item, but we'll also include variety specific info below
            first = items[0]
            
            # Use full text if parsing failed effectively
            if first['growing_info']['culture'] == "N/A" and first['growing_info']['full_text'] != "No growing info available.":
                 # Replace pipes with breaks for readability if we have raw text
                 readable_text = first['growing_info']['full_text'].replace("|", "<br><br><strong>").replace(":", ":</strong>")
                 f.write(f"""
    <section>
        <h2>General Growing Info</h2>
        <p>{readable_text}</p>
    </section>
""")
            elif first['growing_info']['culture'] != "N/A":
                f.write(f"""
    <section>
        <h2>General Culture</h2>
        <p><strong>Soil/Culture:</strong> {first['growing_info']['culture']}</p>
        <p><strong>Pests & Disease:</strong> {first['growing_info']['pests']}</p>
        <p><strong>Harvest:</strong> {first['growing_info']['harvest']}</p>
    </section>
""")
    
            f.write("<h2>Varieties</h2>")
            
            for item in items:
                # Format growing info for individual display
                growing_html = ""
                
                # Check if we have specific parsed info, otherwise use full text
                if item['growing_info']['culture'] == "N/A" and item['growing_info']['full_text'] != "No growing info available.":
                     # Replace pipes with breaks for readability if we have raw text
                     readable_text = item['growing_info']['full_text'].replace(" | ", "<br><br>").replace(":", ":</strong>")
                     # Add initial strong tag if missing from split
                     if not readable_text.startswith("<strong>"):
                         readable_text = "<strong>" + readable_text
                     growing_html = f"<p>{readable_text}</p>"
                else:
                    if item['growing_info']['culture'] != "N/A":
                         growing_html += f"<p><strong>Culture:</strong> {item['growing_info']['culture']}</p>"
                    if item['growing_info']['transplanting'] != "N/A":
                         growing_html += f"<p><strong>Transplanting:</strong> {item['growing_info']['transplanting']}</p>"
                    if item['growing_info']['pests'] != "N/A":
                         growing_html += f"<p><strong>Pests:</strong> {item['growing_info']['pests']}</p>"
                    if item['growing_info']['harvest'] != "N/A":
                         growing_html += f"<p><strong>Harvest:</strong> {item['growing_info']['harvest']}</p>"
                
                f.write(f"""
    <div id="{item['anchor']}" class="variety">
        <h3>{item['name']}</h3>
        {f'<img src="../{item["image"]}" alt="{item["name"]}" style="max-width: 200px; float: right; margin: 0 0 10px 10px; border-radius: 5px;">' if item.get("image") and item["image"] != "N/A" and isinstance(item["image"], str) else ""}
        <p class="meta">
            <strong>Latin Name:</strong> {item['latin']} | 
            <strong>DTM:</strong> {item['dtm']}
        </p>
        <p class="meta">
            <strong>Life Cycle:</strong> {item['lifecycle']} | 
            <strong>Hybrid Status:</strong> {item['hybrid']}
        </p>
        <div class="dates">
            <p><strong>Method:</strong> {item['dates']['method']}</p>
            <p><strong>Start Seeds:</strong> {item['dates']['start_range']}</p>
            <p><strong>Transplant/Sow:</strong> {item['dates']['transplant_range']}</p>
        </div>
        <p><strong>Disease Resistance:</strong> {item['resistance']}</p>
        
        <div class="growing-info">
            <h4>Growing Information</h4>
            {growing_html}
        </div>

        <p><a href="{item['url']}" target="_blank">View on Johnny's Seeds</a></p>
    </div>
""")
            
            f.write("</body></html>")

    # Save Schedule Data
    with open(SCHEDULE_JSON, "w") as f:
        json.dump(schedule_data, f, indent=2)

    # Save Schedule HTML
    json_str = json.dumps(schedule_data, indent=2)
    html_content = SCHEDULE_HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", json_str)
    with open(SCHEDULE_HTML, "w") as f:
        f.write(html_content)

    print(f"Generated {len(grouped)} crop HTML files, schedule data, and schedule.html.")

if __name__ == "__main__":
    main()
