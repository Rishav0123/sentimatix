import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(r'd:\sentimatix\worker-SCRAPE\stock-news\x-news\.env')
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Comprehensive list of major/prominent NSE stocks to verify
MAJOR_STOCKS = {
    # New-age tech / recent IPOs
    'ZOMATO.NS': 'Eternal Limited',
    'NYKAA.NS': 'FSN E-Commerce Ventures Limited',
    'PAYTM.NS': 'One97 Communications Limited',
    'SWIGGY.NS': 'Bundl Technologies Private Limited',
    'POLICYBZR.NS': 'PB Fintech Limited',
    'DELHIVERY.NS': 'Delhivery Limited',
    'CARTRADE.NS': 'CarTrade Tech Limited',
    'MAPMYINDIA.NS': 'CE Info Systems Limited',
    'EASEMYTRIP.NS': 'Easy Trip Planners Limited',
    'IDEAFORGE.NS': 'ideaForge Technology Limited',
    'IXIGO.NS': 'Le Travenues Technology Limited',
    'OLAELEC.NS': 'Ola Electric Mobility Limited',
    'MOBIKWIK.NS': 'Zaak ePayments Services Limited',
    'BLACKBUCK.NS': 'Zinka Logistics Solutions Limited',
    # Large cap blue chips often missed
    'ETERNAL.NS': 'Eternal Limited',
    'UNOMINDA.NS': 'Uno Minda Limited',
    'LODHA.NS': 'Macrotech Developers Limited',
    'NUVAMA.NS': 'Nuvama Wealth Management Limited',
    'SENCO.NS': 'Senco Gold Limited',
    'JSWINFRA.NS': 'JSW Infrastructure Limited',
    'JSWHL.NS': 'JSW Holdings Limited',
    'RATNAVEER.NS': 'Ratnaveer Precision Engineering Limited',
    'KAYNES.NS': 'Kaynes Technology India Limited',
    'SYRMA.NS': 'Syrma SGS Technology Limited',
    'AVALON.NS': 'Avalon Technologies Limited',
    'RATEGAIN.NS': 'RateGain Travel Technologies Limited',
    'ZAGGLE.NS': 'Zaggle Prepaid Ocean Services Limited',
    'HAPPYMIND.NS': 'Happiest Minds Technologies Limited',
    'SAPPHIRE.NS': 'Sapphire Foods India Limited',
    'DEVYANI.NS': 'Devyani International Limited',
    'WESTLIFE.NS': 'Westlife Foodworld Limited',
    'BIKAJI.NS': 'Bikaji Foods International Limited',
    'GOPAL.NS': 'Gopal Snacks Limited',
    'CAMPUS.NS': 'Campus Activewear Limited',
    'BLUESTONE.NS': 'Bluestone Jewellery and Lifestyle Limited',
    'EMCURE.NS': 'Emcure Pharmaceuticals Limited',
    'MANKIND.NS': 'Mankind Pharma Limited',
    'AETHER.NS': 'Aether Industries Limited',
    'HYUNDAI.NS': 'Hyundai Motor India Limited',
    'DOMS.NS': 'DOMS Industries Limited',
    'NTPCGREEN.NS': 'NTPC Green Energy Limited',
    'AFCONS.NS': 'Afcons Infrastructure Limited',
    'GARUDA.NS': 'Garuda Construction and Engineering Limited',
    'DIFFNKG.NS': 'Difference of Opinion Limited',
    'WAKEFIT.NS': 'Wakefit Innovations Private Limited',
    'AWFIS.NS': 'Awfis Space Solutions Limited',
    'JYOTICNC.NS': 'Jyoti CNC Automation Limited',
    'INOXGREEN.NS': 'INOX Green Energy Services Limited',
    # PSU / Government stocks
    'IREDA.NS': 'Indian Renewable Energy Development Agency Limited',
    'IRFC.NS': 'Indian Railway Finance Corporation Limited',
    'RVNL.NS': 'Rail Vikas Nigam Limited',
    'NHPC.NS': 'NHPC Limited',
    'SJVN.NS': 'SJVN Limited',
    'RECLTD.NS': 'REC Limited',
    'PFC.NS': 'Power Finance Corporation Limited',
    'HUDCO.NS': 'Housing and Urban Development Corporation Limited',
    'COCHINSHIP.NS': 'Cochin Shipyard Limited',
    'MIDHANI.NS': 'Mishra Dhatu Nigam Limited',
    'MAZAGON.NS': 'Mazagon Dock Shipbuilders Limited',
    'GRSE.NS': 'Garden Reach Shipbuilders & Engineers Limited',
    'BEL.NS': 'Bharat Electronics Limited',
    'HAL.NS': 'Hindustan Aeronautics Limited',
    'BEML.NS': 'BEML Limited',
}

print("Checking which major stocks are missing from your database...\n")

# Get all existing symbols
existing_res = supabase.table('stocks').select('yfin_symbol').execute()
existing_symbols = {r['yfin_symbol'] for r in existing_res.data}

missing = []
present = []

for symbol, name in MAJOR_STOCKS.items():
    if symbol not in existing_symbols:
        missing.append((symbol, name))
    else:
        present.append(symbol)

print(f"Checked {len(MAJOR_STOCKS)} major stocks")
print(f"Already in DB: {len(present)}")
print(f"MISSING from DB: {len(missing)}\n")

print("Missing stocks:")
for sym, name in missing:
    print(f"  {sym} | {name}")
