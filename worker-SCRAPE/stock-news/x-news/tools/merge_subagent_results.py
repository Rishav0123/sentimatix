import json
import re

def extract_ids_from_url(url):
    pattern = r"stockpricequote/[^/]+/([^/]+)/([^/?#]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def merge_subagent_results():
    # Load Batch 1 results
    with open('final_mapping_100.json', 'r') as f:
        mapping = json.load(f)
    
    # Subagent results (manually copied from the report for accuracy)
    subagent_data = [
        {"name": "DCM Nouvelle", "url": "https://www.moneycontrol.com/india/stockpricequote/textiles/dcmnouvellelimited/DCMNV54272"},
        {"name": "DCM Shriram International", "url": "https://www.moneycontrol.com/india/stockpricequote/textiles/dcmshriraminternational/DSIL"},
        {"name": "Tata Consumer Products", "url": "https://www.moneycontrol.com/india/stockpricequote/plantations-teacoffee/tataconsumerproducts/TT"},
        {"name": "Mahindra & Mahindra", "url": "https://www.moneycontrol.com/india/stockpricequote/auto-carsjeeps/mahindramahindra/MM"},
        {"name": "Macrotech Developers", "url": "https://www.moneycontrol.com/india/stockpricequote/construction-residentialcommercial-complexes/lodhadevelopers/MD03"},
        {"name": "Deccan Gold Mines", "url": "https://www.moneycontrol.com/india/stockpricequote/miningminerals/deccangoldmines/DGM"},
        {"name": "DEE Development Engineers", "url": "https://www.moneycontrol.com/india/stockpricequote/ironsteel/deedevelopmentengineers/DDEL"},
        {"name": "Dharmaj Crop Guard", "url": "https://www.moneycontrol.com/india/stockpricequote/pesticidesagro-chemicals/dharmajcropguard/DCG"},
        {"name": "Deepak Fertilizers", "url": "https://www.moneycontrol.com/india/stockpricequote/fertilisers/deepakfertiliserspetrochemicalscorporation/DFP"},
        {"name": "Deep Industries", "url": "https://www.moneycontrol.com/india/stockpricequote/oil-explorationproduction/deepindustries/DI02"},
        {"name": "GHCL Limited", "url": "https://www.moneycontrol.com/india/stockpricequote/chemicals/gujaratheavychemicals/GHC"},
        {"name": "DELPHI WORLD MONEY", "url": "https://www.moneycontrol.com/india/stockpricequote/finance-investments/delphiworldmoney/WF02"},
        {"name": "Delta Manufacturing", "url": "https://www.moneycontrol.com/india/stockpricequote/electricals/deltamanufacturing/DM04"},
        {"name": "Denta Water", "url": "https://www.moneycontrol.com/india/stockpricequote/infrastructure/dentawaterinfrasolutions/DWISL"},
        {"name": "Dev Information Technology", "url": "https://www.moneycontrol.com/india/stockpricequote/computers-software/devinformationtechnology/DIT02"},
        {"name": "Devyani International", "url": "https://www.moneycontrol.com/india/stockpricequote/consumer-food/devyaniinternational/DI06"},
        {"name": "Hindustan Unilever", "url": "https://www.moneycontrol.com/india/stockpricequote/personal-care/hindustanunilever/HU"},
        {"name": "Dr. Reddys Laboratories", "url": "https://www.moneycontrol.com/india/stockpricequote/pharmaceuticals/drreddyslaboratories/DRL"},
        {"name": "Hindustan Zinc", "url": "https://www.moneycontrol.com/india/stockpricequote/metals-non-ferrous/hindustanzinc/HZ"},
        {"name": "Britannia Industries", "url": "https://www.moneycontrol.com/india/stockpricequote/food-processing/britanniaindustries/BI"},
        {"name": "Divis Laboratories", "url": "https://www.moneycontrol.com/india/stockpricequote/pharmaceuticals/divislaboratories/DL03"},
        {"name": "Dhampur Sugar Mills", "url": "https://www.moneycontrol.com/india/stockpricequote/sugar/dhampursugarmills/DSM"},
        {"name": "20 Microns Limited", "url": "https://www.moneycontrol.com/india/stockpricequote/miningminerals/20microns/2M"},
        {"name": "21st Century Management", "url": "https://www.moneycontrol.com/india/stockpricequote/finance-general/21stcenturymanagementservices/21S"},
        {"name": "360 ONE WAM", "url": "https://www.moneycontrol.com/india/stockpricequote/finance-others/360onewam/IIFLW54277"},
        {"name": "3B Blackbio Dx", "url": "https://www.moneycontrol.com/india/stockpricequote/pesticidesagrochemicals/3bblackbiodx/KI17"},
        {"name": "3P Land Holdings", "url": "https://www.moneycontrol.com/india/stockpricequote/paper/3plandholdings/PI36"},
        {"name": "5Paisa Capital", "url": "https://www.moneycontrol.com/india/stockpricequote/miscellaneous/5paisacapital/C98"},
        {"name": "63 moons technologies", "url": "https://www.moneycontrol.com/india/stockpricequote/computers-software/63moonstechnologies/FT02"},
        {"name": "A2Z Infra Engineering", "url": "https://www.moneycontrol.com/india/stockpricequote/power-transmissionequipment/a2zinfraengineering/AME02"},
        {"name": "Aadhar Housing Finance", "url": "https://www.moneycontrol.com/india/stockpricequote/finance-housing/aadharhousingfinance/AHFL"},
        {"name": "Aarey Drugs", "url": "https://www.moneycontrol.com/india/stockpricequote/pharmaceuticals/areydrugspharmaceuticals/ADP"},
        {"name": "Aaron Industries", "url": "https://www.moneycontrol.com/india/stockpricequote/engineering/aaronindustries/AI79"},
        {"name": "Aarti Industries", "url": "https://www.moneycontrol.com/india/stockpricequote/chemicals/aartiindustries/AI45"},
        {"name": "Aarti Pharmalabs", "url": "https://www.moneycontrol.com/india/stockpricequote/medical-equipmentsuppliesaccessories/aartipharmalabs/AP21"},
        {"name": "Aditya Birla Capital", "url": "https://www.moneycontrol.com/india/stockpricequote/finance-investments/adityabirlacapital/ABC9"},
        {"name": "Allied Blenders", "url": "https://www.moneycontrol.com/india/stockpricequote/breweriesdistilleries/alliedblendersdistillers/ABD"},
        {"name": "Aditya Birla Fashion", "url": "https://www.moneycontrol.com/india/stockpricequote/retail/adityabirlafashionretail/PFR"},
        {"name": "Aditya Birla Lifestyle Brands", "url": "https://www.moneycontrol.com/india/stockpricequote/speciality-retailers/adityabirlalifestylebrands/ABL06"},
        {"name": "ABM International", "url": "https://www.moneycontrol.com/india/stockpricequote/miscellaneous/abminternational/ABM02"},
        {"name": "ABM Knowledgeware", "url": "https://www.moneycontrol.com/india/stockpricequote/computers-software-mediumsmall/abmknowledgeware/ABM"}
    ]
    
    # Simple name matching for merging
    updated_count = 0
    for res in subagent_data:
        mc1, mc2 = extract_ids_from_url(res['url'])
        if not mc1 or not mc2: continue
        
        # Find matching stock in our mapping
        for stock in mapping:
            if stock['Status'] == 'Missing':
                # Check if subagent name is in our NSE name or vice-versa
                if res['name'].lower() in stock['NSE_Name'].lower() or stock['NSE_Name'].lower() in res['name'].lower():
                    stock['MC_Match'] = "FOUND VIA SUBAGENT"
                    stock['MC1'] = mc1
                    stock['MC2'] = mc2
                    stock['Status'] = 'Matched'
                    updated_count += 1
                    break
                    
    # Save updated mapping
    with open('final_mapping_100_v2.json', 'w') as f:
        json.dump(mapping, f, indent=2)
        
    print(f"Merged {updated_count} subagent results.")

if __name__ == "__main__":
    merge_subagent_results()
