import json
import os

mapping_file = 'full_mapping_directory.json'
if not os.path.exists(mapping_file):
    print(f"File {mapping_file} not found.")
else:
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    total = len(mapping)
    matched = sum(1 for x in mapping if x.get('Status') == 'Matched')
    verify = sum(1 for x in mapping if x.get('Status') == 'Verify')
    not_found = sum(1 for x in mapping if x.get('Status') == 'Not Found')
    
    print(f"Total stocks in mapping file: {total}")
    print(f"Status - Matched: {matched}")
    print(f"Status - Verify: {verify}")
    print(f"Status - Not Found: {not_found}")
    
    # Check if they have MC1 and MC2
    has_links = sum(1 for x in mapping if x.get('MC1') and x.get('MC2'))
    print(f"Stocks with both MC links in file: {has_links}")
