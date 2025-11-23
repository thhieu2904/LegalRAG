# 🚀 Vercel Deployment Setup - Frontend

## 📋 Tóm tắt

**Frontend:** React + TypeScript + Vite
**Deployment:** Vercel (recommended for React apps)
**Build:** `npm run build` → `dist/` folder

---

## ✅ BƯỚC 1: Prepare Local Environment

### 1.1. Copy env template

```bash
cd frontend
cp .env.development .env.production
```

### 1.2. Update `.env.production`

```bash
# Production Environment Variables
# Kong Gateway URL on Render
VITE_API_BASE_URL=https://aicenter-kong-gateway.onrender.com
VITE_APP_TITLE=AI Center RAG
VITE_MAX_FILE_SIZE=52428800
```

### 1.3. Test build locally

```bash
# Build production bundle
npm run build

# Preview production build
npm run preview

# Should open at http://localhost:4173
```

---

## 🚀 BƯỚC 2: Deploy to Vercel

### Option A: Via Vercel Dashboard (EASY) ✅

**1. Go to:** https://vercel.com/new

**2. Import Git Repository**

- Select: `aicenter-rag` (GitHub)
- Vercel auto-detects Vite setup

**3. Configure Project**

| Setting              | Value           |
| -------------------- | --------------- |
| **Framework Preset** | Vite            |
| **Root Directory**   | `frontend`      |
| **Build Command**    | `npm run build` |
| **Output Directory** | `dist`          |
| **Install Command**  | `npm install`   |

**4. Environment Variables**

Click **Add Environment Variables** and add:

```
VITE_API_BASE_URL = https://aicenter-kong-gateway.onrender.com
VITE_APP_TITLE = AI Center RAG
VITE_MAX_FILE_SIZE = 52428800
```

**5. Click Deploy**

→ Vercel builds & deploys automatically (~2-5 minutes)

→ You get URL: `https://aicenter-rag.vercel.app`

---

### Option B: Via Vercel CLI (ADVANCED)

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Go to frontend directory
cd frontend

# 3. Deploy to production
vercel --prod

# 4. Follow prompts and confirm environment variables
```

---

## ✅ BƯỚC 3: Verify Deployment

### 3.1. Check Vercel Dashboard

- Go: https://vercel.com/dashboard
- Select project: `aicenter-rag`
- Click **Deployments** tab
- Status should be **READY** ✅

### 3.2. Test Frontend

```bash
# Open in browser
https://aicenter-rag.vercel.app

# Should see:
# - Login page
# - Can login with credentials
# - Can upload documents (if backend ready)
# - Can chat (if backend ready)
```

### 3.3. Check Browser Console

```javascript
// Open DevTools (F12)
// Console tab - should NOT have errors

// Check API base URL
console.log(import.meta.env.VITE_API_BASE_URL);
// Should output: https://aicenter-kong-gateway.onrender.com
```

### 3.4. Test API Connectivity

```bash
# From browser console:
fetch('https://aicenter-kong-gateway.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log(d))

# Should see Kong health response (not CORS error)
```

---

## 🔐 BƯỚC 4: Custom Domain (Optional)

### 4.1. Add Custom Domain

In Vercel Dashboard:

1. Project → **Settings** → **Domains**
2. Click **Add Domain**
3. Enter your domain (e.g., `app.yourdomain.com`)
4. Add DNS records (Vercel provides instructions)

### 4.2. Update Kong CORS

If using custom domain, update Kong env var:

```
FRONTEND_URL=https://app.yourdomain.com
```

Then redeploy Kong on Render.

---

## 📊 Environment Variables Reference

| Variable             | Purpose                 | Value                                        |
| -------------------- | ----------------------- | -------------------------------------------- |
| `VITE_API_BASE_URL`  | Kong Gateway URL        | `https://aicenter-kong-gateway.onrender.com` |
| `VITE_APP_TITLE`     | Browser title           | `AI Center RAG`                              |
| `VITE_MAX_FILE_SIZE` | Max upload size (bytes) | `52428800` (50MB)                            |

**Check frontend usage:**

```bash
# Search where env vars are used
grep -r "VITE_" src/

# Common locations:
# - src/services/api/endpoints.ts
# - src/constants/api.constants.ts
# - src/config/
```

---

## 🔄 BƯỚC 5: Auto-Deploy (Continuous Deployment)

### 5.1. Enable Auto-Deploy (Default)

Vercel automatically redeploys when you push to GitHub:

```bash
# Local machine
git add .
git commit -m "feat: update frontend config"
git push origin feature/rag

# Vercel automatically:
# 1. Triggers build
# 2. Runs tests (if any)
# 3. Deploys to production
# 4. Creates deployment URL
```

### 5.2. Monitor Deployments

In Vercel Dashboard → **Deployments** tab:

- Green checkmark = Success ✅
- Building = In progress ⏳
- Red X = Failed ❌

Click on any deployment to see:

- Build logs
- Function logs (if using serverless)
- Environment variables used

---

## ⚠️ Troubleshooting

### Issue 1: "404 Not Found"

**Nguyên nhân:** Vercel deployed but page shows 404

**Giải pháp:**

1. Check deployment status (should be READY)
2. Try refresh page (Ctrl+Shift+R)
3. Check build logs for errors

### Issue 2: "CORS Error"

**Nguyên nhân:** Frontend can't reach Kong gateway

**Giải pháp:**

1. Check `VITE_API_BASE_URL` is correct
2. Verify Kong is running on Render
3. Check Kong CORS config includes `https://aicenter-rag.vercel.app`

### Issue 3: "Blank page"

**Nguyên nhân:** Build failed or JS error

**Giải pháp:**

1. Check browser console (F12)
2. Check Vercel build logs
3. Verify all dependencies installed

### Issue 4: "API not responding"

**Nguyên nhân:** Backend services not running

**Giải pháp:**

1. Check Render services status
2. Check Kong health: `https://aicenter-kong-gateway.onrender.com/health`
3. Check firewall rules

---

## 📝 Build & Deployment Flow

```
Local Development
    ↓ (git push)
GitHub Repository
    ↓ (webhook trigger)
Vercel Build
    ├─ npm install
    ├─ npm run build
    └─ tsc -b && vite build
    ↓
Vercel CDN
    ↓
Browser requests
    ↓ (API calls)
Kong Gateway
    ↓
Backend Services
```

---

## 🔗 Useful Links

- **Vercel Docs:** https://vercel.com/docs
- **Vite Docs:** https://vitejs.dev
- **React Docs:** https://react.dev
- **Env Variables in Vite:** https://vitejs.dev/guide/env-and-mode

---

## 📋 Deployment Checklist

- [ ] `.env.production` created with correct `VITE_API_BASE_URL`
- [ ] `npm run build` succeeds locally
- [ ] `npm run preview` works (test locally)
- [ ] GitHub account linked to Vercel
- [ ] Repository pushed to GitHub
- [ ] Vercel project created
- [ ] Environment variables set in Vercel dashboard
- [ ] Build completes successfully (status = READY)
- [ ] Frontend loads: `https://aicenter-rag.vercel.app`
- [ ] API connectivity works (no CORS errors)
- [ ] Kong gateway configured with frontend URL in CORS

---

## 🎉 Success!

When everything is set up correctly:

1. **Frontend URL:** `https://aicenter-rag.vercel.app` ✅
2. **API Gateway:** `https://aicenter-kong-gateway.onrender.com` ✅
3. **Backend Services:** All running on Render ✅
4. **Database:** Supabase with Connection Pooler ✅

**System is fully deployed and ready for production!** 🚀
