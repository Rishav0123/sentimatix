import os, sys
sys.path.append(os.getcwd())
from utilities.get_active_stocks import get_active_stocks
stocks = get_active_stocks()
for s in stocks[:5]:
    print(f"{s['yfin_symbol']} -> mc_link_1: '{s.get('mc_link_1')}', mc_link_2: '{s.get('mc_link_2')}'")
