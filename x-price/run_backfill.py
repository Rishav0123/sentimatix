#!/usr/bin/env python3
"""
Run comprehensive backfill for all stocks
This script will backfill historical data from 2020-01-01 to today
"""

import subprocess
import sys
from datetime import datetime

def run_comprehensive_backfill():
    """Run the optimized backfill for all stocks"""
    print("🚀 Starting comprehensive backfill for all 100 stocks")
    print("📅 Date range: 2020-01-01 to today (excluding existing data)")
    print("⚡ Features: gap detection, batch inserts, intelligent date ranges")
    print()
    
    # Confirm with user
    response = input("This will process all 100 stocks and may take 30-60 minutes. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Backfill cancelled by user")
        return
    
    print("\n⏰ Starting backfill process...")
    start_time = datetime.now()
    
    try:
        # Run the optimized backfill script
        result = subprocess.run([
            sys.executable, 
            "optimized_backfill.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Backfill completed in {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"📊 Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("🎉 Backfill completed successfully!")
        else:
            print("⚠️  Backfill completed with some issues")
            
    except Exception as e:
        print(f"❌ Error running backfill: {e}")

def show_help():
    """Show help information"""
    print("Comprehensive Stock Price Backfill Tool")
    print("=" * 40)
    print()
    print("Commands:")
    print("  python run_backfill.py              - Run full backfill for all stocks")
    print("  python run_backfill.py --dry-run    - Show what would be done (no actual data)")
    print("  python run_backfill.py --help       - Show this help")
    print()
    print("Direct optimized backfill options:")
    print("  python optimized_backfill.py --dry-run --stock-limit 5")
    print("  python optimized_backfill.py --stock-limit 10")
    print("  python optimized_backfill.py")
    print()
    print("Features:")
    print("  ✅ Smart gap detection (excludes existing data)")
    print("  ✅ Batch operations for performance")
    print("  ✅ Handles weekends/holidays automatically")
    print("  ✅ Starts from stock listing date or 2020-01-01")
    print("  ✅ Comprehensive logging")

def run_dry_run():
    """Run a dry run to show what would be done"""
    print("🔍 Running dry run to analyze gaps...")
    
    try:
        result = subprocess.run([
            sys.executable, 
            "optimized_backfill.py", 
            "--dry-run"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
    except Exception as e:
        print(f"❌ Error running dry run: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            show_help()
        elif sys.argv[1] == '--dry-run':
            run_dry_run()
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for available options")
    else:
        run_comprehensive_backfill()