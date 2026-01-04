# Deploy notes for backend

Required environment variables

- SUPABASE_URL: Your Supabase project URL (e.g. https://your-project-id.supabase.co)
- SUPABASE_KEY: Supabase anon or service role key
- GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET: (optional) for Google OAuth
- VITE_API_KEY: (optional) client-side API key for UI features

If you're deploying to Render (https://render.com):

- **Tip:** Use **Python 3.11** for the service runtime to avoid building pandas from source (Python 3.13 may not have prebuilt pandas wheels). You can change the runtime in the Render dashboard under Service > Environment > Runtime.
- **Alternative:** Deploy using Docker — a `backend/Dockerfile` is included which uses Python 3.11 to ensure consistent, reproducible builds.

1. Go to your service > Environment > Environment Variables
2. Add `SUPABASE_URL` and `SUPABASE_KEY` (and any other keys needed)
3. Redeploy the service

If you prefer local development, copy `backend/.env.example` to `.env` and fill values.

A small helper script is available to programmatically set environment variables for a Render service from a local `.env` file: `scripts/set_render_env.py`.

Example (dry-run):
```bash
python scripts/set_render_env.py --service-id <SERVICE_ID> --env-file backend/.env --keys SUPABASE_URL,SUPABASE_KEY
```

Example (apply changes):
```bash
python scripts/set_render_env.py --service-id <SERVICE_ID> --api-key $RENDER_API_KEY --env-file backend/.env --keys SUPABASE_URL,SUPABASE_KEY --apply
```

Security note: treat keys as secrets. Rotate keys immediately if ever committed accidentally.
