import os, json, re

PLUGIN_DIR = "plugins"
ICON_DIR = "icons"
OUTPUT_FILE = "plugins.json"

# Pattern to match metadata lines
metadata_pattern = re.compile(r'__plugin_(name|author|version|description)__\s*=\s*["\'](.+?)["\']')

plugins_data = []

for filename in os.listdir(PLUGIN_DIR):
    if filename.endswith(".py"):
        plugin_path = os.path.join(PLUGIN_DIR, filename)
        with open(plugin_path, "r", encoding="utf-8") as f:
            content = f.read()

        meta_matches = dict(re.findall(metadata_pattern, content))
        
        if all(k in meta_matches for k in ["name", "author", "version", "description"]):
            icon_file = filename.replace(".py", ".png")
            icon_url = f"https://raw.githubusercontent.com/AidenZaire/algebytestore/main/{ICON_DIR}/{icon_file}"
            download_url = f"https://raw.githubusercontent.com/AidenZaire/algebytestore/main/{PLUGIN_DIR}/{filename}"

            plugins_data.append({
                "name": meta_matches["name"],
                "author": meta_matches["author"],
                "version": meta_matches["version"],
                "description": meta_matches["description"],
                "icon_url": icon_url,
                "download_url": download_url
            })

# Save plugins.json
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(plugins_data, f, indent=2)

print(f"✅ Generated {OUTPUT_FILE} with {len(plugins_data)} plugins.")

Add plugin auto-update script
