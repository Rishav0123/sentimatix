# Deploy notes for backend

Required environment variables

- SUPABASE_URL: Your Supabase project URL (e.g. https://your-project-id.supabase.co)
- SUPABASE_KEY: Supabase anon or service role key
- GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET: (optional) for Google OAuth
- VITE_API_KEY: (optional) client-side API key for UI features

If you're deploying to Render (https://render.com):

1. Go to your service > Environment > Environment Variables
2. Add `SUPABASE_URL` and `SUPABASE_KEY` (and any other keys needed)
3. Redeploy the service

If you prefer local development, copy `backend/.env.example` to `.env` and fill values.

Security note: treat keys as secrets. Rotate keys immediately if ever committed accidentally.
