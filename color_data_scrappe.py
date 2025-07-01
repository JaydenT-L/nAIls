
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

BASE_URL = "https://www.dndgel.com/collections/dnd-duo?page={}"
SAVE_DIR = "dnd_duo_data"
os.makedirs(SAVE_DIR, exist_ok=True)
all_data = []

def get_rgb_hex_from_image(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((1, 1))
        r, g, b = img.getpixel((0, 0))
        return (r, g, b), '#{:02X}{:02X}{:02X}'.format(r, g, b)
    except:
        return (0, 0, 0), "#000000"

for page in range(1, 13):
    print(f"Scraping page {page}...")
    res = requests.get(BASE_URL.format(page))
    soup = BeautifulSoup(res.text, "html.parser")

    products = soup.select("li.grid__item")
    if not products:
        print("⚠️ No products found on this page!")
        continue

    for product in products:
        try:
            name_tag = product.select_one("div.card__content h3.card__heading")
            if not name_tag:
                continue
            full_name = name_tag.text.strip().replace("\n", " ")
            full_name = re.sub(r"- Final Sale", "", full_name, flags=re.IGNORECASE).strip()

            # Try match: starts with number
            match = re.match(r"^(\d+)\s+(.*)", full_name)
            if match:
                shade_number = match.group(1)
                color_name = match.group(2)
            else:
                # Try match: ends with hashtag number
                match_end = re.match(r"^(.*)\s+#(\d+)$", full_name)
                if match_end:
                    color_name = match_end.group(1).strip()
                    shade_number = match_end.group(2)
                else:
                    shade_number = "000"
                    color_name = full_name.strip()

            color_name = re.sub(r"\s+", " ", color_name)  # remove double spaces


            folder_name = f"{shade_number}_{color_name.replace(' ', '_')}"
            folder_path = os.path.join(SAVE_DIR, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            img_tag = product.select_one("img")
            if not img_tag or not img_tag.get("src"):
                continue

            img_url = img_tag["src"]
            if img_url.startswith("//"):
                img_url = "https:" + img_url

            image_path = os.path.join(folder_path, "1.jpg")
            img_data = requests.get(img_url).content
            with open(image_path, "wb") as f:
                f.write(img_data)

            rgb, hex_color = get_rgb_hex_from_image(img_url)

            all_data.append({
                "shade_number": shade_number,
                "color_name": color_name,
                "hex": hex_color,
                "rgb": rgb,
                "images": [image_path]
            })
            print(f"✔ Saved {shade_number} {color_name}")
        except Exception as e:
            print("❌ Error:", e)

# Save to JSON
json_path = os.path.join(SAVE_DIR, "dnd_colors.json")
with open(json_path, "w") as f:
    json.dump(all_data, f, indent=2)

print("✅ Done. Data saved to", json_path)
