import os
import json
import urllib.parse
import requests
from jinja2 import Environment, FileSystemLoader

def get_tiktok_embed_html(tiktok_url):
    """Fetches the TikTok oEmbed HTML for a given URL."""
    api_url = f"https://www.tiktok.com/oembed?url={tiktok_url}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json().get('html')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TikTok oEmbed data: {e}")
        return None

def generate_cafe_navigation(all_cafes_data, template_env):
    """Generates the reusable cafe navigation HTML file in the root directory."""
    print("\n--- Generating cafe navigation HTML ---")
    try:
        template = template_env.get_template("_cafe_navigation_template.html")
        nav_html_content = template.render(cafes=all_cafes_data)
        with open("_cafe_navigation.html", "w", encoding="utf-8") as f:
            f.write(nav_html_content)
        print("Cafe navigation HTML generated successfully in root directory.")
    except Exception as e:
        print(f"Error generating cafe navigation HTML: {e}")

def generate_cafe_page(cafe_data, template_env):
    """Generates an individual HTML page for a single cafe."""
    cafe_id = cafe_data['id']
    output_dir = cafe_id
    os.makedirs(output_dir, exist_ok=True)

    # Prepare data for template
    if cafe_data.get('google_maps_place_url'):
        cafe_data['google_maps_url'] = cafe_data['google_maps_place_url']
    else:
        cafe_data['google_maps_url'] = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(cafe_data['address'])}"

    # Generate Google Maps Embed URL (API Key NOT required for basic embed)
    if cafe_data.get('address'):
        cafe_data['google_maps_embed_url'] = f"https://maps.google.com/maps?q={urllib.parse.quote(cafe_data['address'])}&output=embed"
    else:
        cafe_data['google_maps_embed_url'] = ""
    
    image_paths = []
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        image_files = sorted(
            [f for f in files if f.startswith(f"{cafe_id}_cafe_image_") and f.endswith('.jpg')],
            key=lambda x: int(x.split('_')[-1].split('.')[0])
        )
        for img_file in image_files:
            # Path relative to the individual cafe's HTML file
            img_path = os.path.join('./', img_file)
            image_paths.append(img_path.replace('\\', '/'))
    cafe_data['image_paths'] = image_paths

    print(f"Fetching TikTok embed code for {cafe_data['name']}...")
    cafe_data['embed_html'] = get_tiktok_embed_html(cafe_data['tiktok_url'])

    # Generate HTML for individual cafe page
    try:
        template = template_env.get_template("template.html")
        html_content = template.render(cafe=cafe_data)

        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated {output_dir}/index.html successfully.")
    except Exception as e:
        print(f"Error generating HTML for {cafe_id}: {e}")

def generate_main_index(cafes_data, template_env):
    """Generates the main index.html page with links to individual cafe pages."""
    print("\n--- Generating main index.html ---")
    try:
        # Generate embed URL for all cafes
        all_addresses = [cafe['address'] for cafe in cafes_data if cafe.get('address') and cafe['address'] != "不明"]
        all_cafes_map_embed_url = ""
        if all_addresses:
            # For multiple markers, use the directions API or a custom map. 
            # For simple embed, we can try to combine addresses or focus on a central point.
            # A more robust solution would involve Google Maps JavaScript API or Static Maps API.
            # For now, we'll create a query for all addresses.
            query_string = "+".join([urllib.parse.quote(addr) for addr in all_addresses])
            all_cafes_map_embed_url = f"https://maps.google.com/maps?q={query_string}&output=embed"

        template = template_env.get_template("main_index_template.html")
        html_content = template.render(cafes=cafes_data, all_cafes_map_embed_url=all_cafes_map_embed_url)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Main index.html generated successfully.")
    except Exception as e:
        print(f"Error generating main index.html: {e}")

def main():
    try:
        with open("cafes.json", "r", encoding="utf-8") as f:
            cafes_data = json.load(f)
    except FileNotFoundError:
        print("Error: cafes.json not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode cafes.json. Please check its format.")
        return

    env = Environment(loader=FileSystemLoader('.'))
    # Add truncate filter for main index page description
    env.filters['truncate'] = lambda s, length, killwords, end: s[:length] + (end if len(s) > length else '')

    # Generate reusable cafe navigation HTML first
    generate_cafe_navigation(cafes_data, env)

    for cafe in cafes_data:
        generate_cafe_page(cafe, env)
    
    generate_main_index(cafes_data, env)

if __name__ == "__main__":
    main()