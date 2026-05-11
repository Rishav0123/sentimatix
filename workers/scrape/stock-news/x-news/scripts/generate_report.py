import os
import json
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

def parse_metric_details(val):
    """Parses metric value which can be int or string 'inserted:X skipped:Y'."""
    inserted = 0
    skipped = 0
    if isinstance(val, int):
        inserted = val
    elif isinstance(val, str) and "inserted:" in val:
        try:
            parts = val.split()
            for p in parts:
                if p.startswith('inserted:'):
                    inserted = int(p.split(':')[1])
                elif p.startswith('skipped:'):
                    skipped = int(p.split(':')[1])
        except:
            pass
    return inserted, skipped

def generate_report(days=1):
    load_dotenv()
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase = create_client(url, key)
    
    # Calculate cutoff time
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    try:
        # Fetch reports in the last N days
        response = supabase.table('scraper_reports').select("*").gte('timestamp', cutoff).order('timestamp', desc=True).execute()
        
        if not response.data:
            print(f"No reports found in the last {days} day(s).")
            return

        reports = response.data
        
        # Group by run_id
        runs = {}
        for r in reports:
            rid = r['run_id']
            if rid not in runs:
                runs[rid] = {
                    'timestamp': r['timestamp'],
                    'scrapers': {},
                    'total_inserted': 0,
                    'total_skipped': 0,
                    'stock_totals': {}
                }
            
            scraper_name = r['scraper_name']
            stock_counts = r['stock_counts'] or {}
            
            s_inserted = 0
            s_skipped = 0
            
            for sym, val in stock_counts.items():
                ins, skip = parse_metric_details(val)
                s_inserted += ins
                s_skipped += skip
                
                if sym not in runs[rid]['stock_totals']:
                    runs[rid]['stock_totals'][sym] = {'inserted': 0, 'skipped': 0}
                runs[rid]['stock_totals'][sym]['inserted'] += ins
                runs[rid]['stock_totals'][sym]['skipped'] += skip

            runs[rid]['scrapers'][scraper_name] = {'inserted': s_inserted, 'skipped': s_skipped}
            runs[rid]['total_inserted'] += s_inserted
            runs[rid]['total_skipped'] += s_skipped

        # Generate output
        report_dir = Path("logs/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = report_dir / report_filename
        
        with open(report_path, 'w') as f:
            f.write(f"# Scraper Activity Report (Last {days} Day(s))\n\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for rid, data in runs.items():
                f.write(f"## Run ID: `{rid}`\n")
                f.write(f"**Timestamp:** {data['timestamp']}\n\n")
                
                f.write("### Scraper Performance\n")
                f.write("| Scraper | Articles Inserted | Articles Skipped (Dedup) |\n")
                f.write("| :--- | :--- | :--- |\n")
                for s_name, s_data in data['scrapers'].items():
                    f.write(f"| {s_name} | {s_data['inserted']} | {s_data['skipped']} |\n")
                f.write(f"| **Total** | **{data['total_inserted']}** | **{data['total_skipped']}** |\n\n")
                
                f.write("### Top 10 Stocks by Coverage (Inserted)\n")
                top_stocks = sorted(data['stock_totals'].items(), key=lambda x: x[1]['inserted'], reverse=True)[:10]
                f.write("| Stock | Inserted | Skipped |\n")
                f.write("| :--- | :--- | :--- |\n")
                for sym, counts in top_stocks:
                    if counts['inserted'] > 0 or counts['skipped'] > 0:
                        f.write(f"| {sym} | {counts['inserted']} | {counts['skipped']} |\n")
                
                f.write("\n---\n\n")
        
        print(f"Report generated successfully: {report_path}")
        
        # Also print a quick summary to terminal
        print("\n--- QUICK SUMMARY ---")
        for rid, data in runs.items():
            print(f"Run {rid[:8]}... | {data['timestamp']} | Total: {data['total_inserted']} inserted, {data['total_skipped']} skipped")
            top_3 = ", ".join([f"{s} (Ins:{c['inserted']} Skip:{c['skipped']})" for s, c in sorted(data['stock_totals'].items(), key=lambda x: x[1]['inserted'], reverse=True)[:3]])
            print(f"  Top Stocks: {top_3}")
            
    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    import sys
    days_arg = 1
    if len(sys.argv) > 1:
        try:
            days_arg = int(sys.argv[1])
        except:
            pass
    generate_report(days_arg)
