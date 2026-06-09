# Frontend Dashboard MVP

Dashboard and create-profile form built with Next.js and connected directly to Supabase.

## What it includes

- `Dashboard` page with:
  - summary cards
  - searchable/sortable profiles table
- `Create Profile` page with:
  - `profile_name`
  - `name`
  - `linkedin_url`
  - duplicate validation against the real Supabase dataset

## Local run

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

Then fill in:

```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

Then run:

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Vercel deployment

1. Push this repo to GitHub
2. Import the repo into Vercel
3. Set the project root directory to `frontend`
4. Deploy

## Current data source

This frontend reads and writes directly to the real Supabase `profiles` table using:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Expected table fields

The UI expects these fields on `profiles`:

```text
id
profile_name
name
linkedin_url
last_connections_number
last_checked_at
active
created_at
```

## Validation rules

The create form blocks submission when:

- `profile_name` already exists
- `linkedin_url` already exists
