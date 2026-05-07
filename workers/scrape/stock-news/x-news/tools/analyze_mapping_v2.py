import json
import os
from collections import Counter

mapping_file = 'full_mapping_directory.json'
with open(mapping_file, 'r') as f:
    mapping = json.load(f)

statuses = Counter(x.get('Status') for x in mapping)
print("Statuses in mapping file:")
for status, count in statuses.items():
    print(f"  {status}: {count}")

has_links = sum(1 for x in mapping if x.get('MC1') and x.get('MC2'))
print(f"\nStocks with both MC links: {has_links} / {len(mapping)}")

# Check a sample of those without links
no_links = [x for x in mapping if not (x.get('MC1') and x.get('MC2'))]
if no_links:
    print("\nSample of stocks without links:")
    for x in no_links[:5]:
        print(f"  {x.get('Symbol')} - Status: {x.get('Status')}")
