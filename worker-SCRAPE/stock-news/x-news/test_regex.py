import re
kw = 'divis'
title = 'Northwestern University Promotes Three in Business and Finance Division'
pattern = r'\b' + re.escape(kw) + r'\b'
match = re.search(pattern, title.lower())
print(f"Match found: {bool(match)}")
