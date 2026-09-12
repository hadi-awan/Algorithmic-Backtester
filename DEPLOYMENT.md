# Deployment Guide

This project deploys as two independent pieces: the FastAPI backend on
Render (native Python, no Docker needed) and the React frontend on
Vercel. Both are configured to deploy straight from this GitHub repo.

## 0. Push this repo to GitHub (one-time)

From the project root:

```bash
git add .
git commit -m "Initial commit: quant signal backtester v1"
```

Then create a new, empty repository on GitHub (github.com/new -- do
**not** initialize it with a README/.gitignore, since this repo already
has content), and push:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 1. Deploy the backend to Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign
   in with GitHub (creates your account on first login).
2. Click **New +** -> **Blueprint**.
3. Select this repo. Render will detect `render.yaml` at the repo root
   and propose a service called `quant-backtester-api` -- confirm and
   deploy.
4. Wait for the first build to finish (installs `backend/requirements.txt`,
   including scikit-learn -- can take a few minutes on the free tier).
5. Once live, copy the service's public URL, e.g.
   `https://quant-backtester-api.onrender.com`.
6. Sanity check it directly: visit
   `https://quant-backtester-api.onrender.com/api/health` -- you should
   see `{"status":"ok"}`.

**Free tier note:** Render's free web services spin down after a period
of inactivity. The first request after idling can take 30-50 seconds to
wake back up -- worth mentioning in the README so a recruiter clicking
the demo cold doesn't think it's broken, just slow to wake up.

## 2. Deploy the frontend to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New** -> **Project**, select this same repo.
3. In the import settings, set **Root Directory** to `frontend`. Vercel
   should auto-detect the Vite framework preset from `frontend/vercel.json`.
4. Add an environment variable before deploying:
   - `VITE_API_URL` = the Render URL from step 1
     (e.g. `https://quant-backtester-api.onrender.com`)
5. Deploy. Once live, copy the frontend's URL, e.g.
   `https://your-app.vercel.app`.

## 3. Lock down CORS on the backend

Right now `render.yaml` sets `CORS_ALLOWED_ORIGINS` to `*` so nothing is
blocked while you're wiring things up. Once you have the real Vercel
URL:

1. In the Render dashboard, open the `quant-backtester-api` service ->
   **Environment**.
2. Set `CORS_ALLOWED_ORIGINS` to your Vercel URL (comma-separate
   additional origins if you want to keep hitting the deployed API from
   local dev too):
   ```
   https://your-app.vercel.app,http://localhost:5173
   ```
3. Save -- Render will redeploy the service with the new setting.

## 4. Verify end to end

Open the Vercel URL in a browser, run a backtest with a real ticker,
and confirm:
- Results load (equity curves, metrics, feature importances, trade logs).
- No CORS errors in the browser console/network tab.
- If the backend was idle, the first request may just take a while
  (see the free-tier note above) rather than failing outright.

## Updating either deployment later

Both Render and Vercel are connected directly to this GitHub repo, so a
`git push` to `main` triggers a new deploy on each automatically -- no
manual redeploy step needed for routine changes.
