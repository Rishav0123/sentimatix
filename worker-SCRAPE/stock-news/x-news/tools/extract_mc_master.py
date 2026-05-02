import os
import re
import json

def extract_from_markdown():
    base_dir = r"C:\Users\risha\.gemini\antigravity\brain\8f2729f4-0adc-4b97-b006-cf80289817e8\.system_generated\steps"
    master_directory = {}
    
    # Pattern to match [Name](URL) where URL contains moneycontrol stockpricequote
    # Example: [A B Infrabuild](https://www.moneycontrol.com/india/stockpricequote/infrastructuregeneral/abinfrabuild/I07)
    link_pattern = r"\[([^\]]+)\]\((https://www\.moneycontrol\.com/india/stockpricequote/[^\)]+)\)"
    
    for folder in os.listdir(base_dir):
        content_path = os.path.join(base_dir, folder, "content.md")
        if os.path.exists(content_path):
            print(f"Processing {content_path}...")
            try:
                with open(content_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(link_pattern, content)
                    for name, url in matches:
                        master_directory[name.strip()] = url
            except Exception as e:
                print(f"Error reading {content_path}: {e}")
                
    output_file = 'mc_master_mapping.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_directory, f, indent=2)
    
    print(f"\nExtraction complete! Total stocks found: {len(master_directory)}")
    print(f"Mapping saved to {output_file}")

if __name__ == "__main__":
    extract_from_markdown()
