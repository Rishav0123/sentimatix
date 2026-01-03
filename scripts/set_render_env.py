#!/usr/bin/env python3
"""
set_render_env.py

Utility to set environment variables on a Render service from a local .env file.

Usage examples:
  # Preview changes (no API key required)
  python scripts/set_render_env.py --service-id <SERVICE_ID> --env-file backend/.env --keys SUPABASE_URL,SUPABASE_KEY

  # Apply changes (will perform authenticated API calls)
  python scripts/set_render_env.py --service-id <SERVICE_ID> --api-key <RENDER_API_KEY> --env-file backend/.env --keys SUPABASE_URL,SUPABASE_KEY --apply

Notes:
- The script defaults to dry-run (no API requests) unless `--apply` is passed.
- It will only send keys present in the env file (and matching `--keys` if provided).
- Sensitive values are masked in output unless you pass `--show` (avoid doing that in shared logs).
- I will not run this script without your explicit consent and API credentials.
"""

from pathlib import Path
import argparse
import sys
import json

try:
    import requests
except Exception as e:
    print("This script requires the 'requests' package. Install with: pip install requests")
    raise

try:
    from dotenv import dotenv_values
except Exception:
    def dotenv_values(path):
        # Minimal fallback parser (no interpolation)
        data = {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")
        return data

SENSITIVE_KEYS_HINT = {"KEY", "SECRET", "TOKEN", "PASSWORD"}

parser = argparse.ArgumentParser(description="Set env vars on Render from a local env file (dry-run by default).")
parser.add_argument('--service-id', required=True, help='Render service id')
parser.add_argument('--api-key', required=False, help='Render API key (required for --apply)')
parser.add_argument('--env-file', default='backend/.env', help='Path to env file (default: backend/.env)')
parser.add_argument('--keys', default='SUPABASE_URL,SUPABASE_KEY', help='Comma-separated list of keys to set (default: SUPABASE_URL,SUPABASE_KEY)')
parser.add_argument('--apply', action='store_true', help='Actually perform API calls. Without this the script does a dry-run.')
parser.add_argument('--show', action='store_true', help='Show full values in output (avoid in public logs).')
args = parser.parse_args()

env_path = Path(args.env_file)
if not env_path.exists():
    print(f"Env file not found: {env_path}")
    sys.exit(1)

env = dotenv_values(env_path)
keys = [k.strip() for k in args.keys.split(',') if k.strip()]
payload = []
for k in keys:
    if k in env and env[k] != "":
        v = env[k]
        sensitive = any(tok in k.upper() for tok in SENSITIVE_KEYS_HINT) or k.upper().endswith("_KEY")
        payload.append({"key": k, "value": v, "sensitive": bool(sensitive)})

if not payload:
    print("No keys found in the env file matching the requested keys. Nothing to do.")
    sys.exit(0)

print("Planned changes:")
for item in payload:
    display_val = item['value'] if args.show else ('***' if item['sensitive'] else item['value'])
    print(f"  - {item['key']} = {display_val} (sensitive={item['sensitive']})")

if not args.apply:
    print("\nDry-run mode. No API requests were made. Re-run with --apply and provide --api-key to apply the changes.")
    sys.exit(0)

if not args.api_key:
    print("--apply was requested but no --api-key was provided. Exiting.")
    sys.exit(1)

url = f"https://api.render.com/v1/services/{args.service_id}/env-vars"
headers = {
    'Authorization': f'Bearer {args.api_key}',
    'Content-Type': 'application/json'
}

# Render's API accepts a JSON array of {key,value,sensitive} objects.
resp = requests.post(url, headers=headers, json=payload)

if resp.status_code in (200, 201):
    print("Successfully applied env vars to Render service.")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    sys.exit(0)
else:
    print(f"Failed to apply env vars. HTTP {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    sys.exit(2)
