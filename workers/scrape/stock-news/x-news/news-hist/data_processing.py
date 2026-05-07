import pandas as pd
from datetime import datetime
import pytz

# Load your CSV
df = pd.read_csv("matched_news.csv")  # Replace with your actual filename

# Assume the column with dates is named 'raw_date'
def convert_to_timestamp(date_str):
    print(type(date_str), date_str)
    try:
        # Remove the weekday part
        cleaned = ','.join(date_str.split(',')[:2]).strip()
        # Parse to datetime
        dt = datetime.strptime(cleaned, "%B %d, %Y")
        # Add default time and convert to UTC
        dt = dt.replace(hour=16, minute=28, second=0)
        dt_utc = dt.astimezone(pytz.UTC)
        return dt_utc.isoformat()
    except Exception as e:
        print(f"Error parsing '{date_str}': {e}")
        return None

# Apply conversion
df["scraped_at"] = df["Date"].apply(convert_to_timestamp)

# Save to new CSV
df.to_csv("converted_dates.csv", index=False)