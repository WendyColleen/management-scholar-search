# ManagementScholarSearch (zero-cost hosting)

This project is designed for **free public hosting** with **manual daily updates**:

**Workflow:**
1) Run `python generate_site.py` on your computer (once a day, or whenever).
2) `git push` to GitHub.
3) Your website updates automatically via **GitHub Pages**.

No VPS, no always-on server.

---

## What you get
- A public website listing **funding / CFPs / conferences / journal items**
- Client-side filters by **region** and **type**
- A static **RSS feed** for a newsletter (`/feeds/newsletter.xml`)
- A discrete AdSense sidebar slot (optional)

---

## 1) One-time setup (your computer)

### A. Install Python
Install Python 3.11+ from python.org (and check “Add python to PATH”).

### B. Download this project
Unzip it to a folder, e.g.:
`C:\Users\wefarrell\Downloads\managementscholarsearch`

### C. Create your `.env`
In PowerShell (inside the project folder):

```powershell
copy .env.example .env
notepad .env
```

Minimum recommended values:
- `DB_PATH=./data/mss.sqlite` (already in `.env.example`)
- `DOMAIN_NAME=managementscholarsearch.com`
- `PUBLIC_BASE_URL=https://managementscholarsearch.com` (once your domain is live)

Optional:
- `OPENAI_API_KEY=...` (nicer summaries)
- `ADSENSE_CLIENT_ID=ca-pub-...`
- `ADSENSE_AD_SLOT=...`
- `MAILERLITE_FORM_URL=...` (link to your MailerLite signup form)

### D. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## 2) Daily update (the only thing you do)

```powershell
python generate_site.py
```

This generates a static site into `./docs/`:
- `docs/index.html`
- `docs/assets/items.json`
- `docs/feeds/newsletter.xml`

Commit + push those generated files:

```powershell
git add docs
git commit -m "Daily update"
git push
```

---

## 3) Publish for free with GitHub Pages (one-time)

1) Create a GitHub repo (private or public).
2) Push this project to the repo.
3) In GitHub: **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: `main`
   - Folder: `/docs`

After that, GitHub will give you a URL like:
`https://YOURNAME.github.io/REPO/`

---

## 4) Point your custom domain (managementscholarsearch.com)

Where you manage DNS:
- Create an **A record** for `@` pointing to GitHub Pages IPs
- Create a **CNAME** for `www` pointing to your GitHub Pages domain

GitHub’s Pages docs show the current IPs and recommended DNS settings.

This project also writes `docs/CNAME` automatically from `DOMAIN_NAME`.

---

## Newsletter RSS
Your RSS file is generated here:

- `https://managementscholarsearch.com/feeds/newsletter.xml`

You can plug this into an RSS-to-email newsletter tool, or copy/paste manually.

---

## Add / change sources
Edit:
`app/sources/sources.yaml`

Then rerun:
`python generate_site.py`

---

## Troubleshooting

### Nothing shows on the site
Run `python generate_site.py` at least once and ensure `docs/index.html` was created.

### Ads don’t show
- AdSense can take time to approve a domain.
- Ensure you set both `ADSENSE_CLIENT_ID` and `ADSENSE_AD_SLOT`.

### I still want the Docker web app
The original Docker web app is still in the repo (FastAPI + worker). You can use it later if/when you decide to move to a VPS.
