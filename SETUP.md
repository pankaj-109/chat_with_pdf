# Setup Guide — Chat with PDF (Full-Stack Web App)

This guide takes you from a **completely fresh computer** to the **Chat with PDF web
app running in your browser**. No prior experience assumed — every step is spelled out
for Windows, macOS, and Linux.

This app has **two parts** that run at the same time, in **two separate terminals**:

- a **backend** (Python / FastAPI) — the brain: reads PDFs, talks to Gemini, stores data
- a **frontend** (Node / React / Vite) — the website you see in the browser

You'll start the backend first, then the frontend, then open the page. If you get
stuck, see [Troubleshooting](#10-troubleshooting).

---

## 0. What you'll need

You create **one** free key along the way: a **Google Gemini API key**. (Unlike the
Telegram bot, there's no login and no Telegram account needed — each browser just gets
an anonymous session.)

Total time: ~25–35 minutes the first time.

> **Words you'll see a lot:**
> - **Terminal** — the text window where you type commands (PowerShell on Windows,
>   Terminal on macOS, your shell on Linux).
> - **Backend / frontend** — the two halves above. Each runs in its own terminal and
>   keeps running while you use the app.
> - **Virtual environment (venv)** — a private folder holding the backend's Python
>   packages so they don't clash with anything else.
> - **`localhost:8000` / `localhost:5173`** — addresses on *your own machine*. 8000 is
>   the backend, 5173 is the website.
> - **API key** — a secret password for talking to Gemini. Treat it like a password.

---

## 1. Install the prerequisites

You need three tools: **Python 3.11 or 3.12**, **Node.js 18+**, and (to download the
project) **Git**.

> ⚠️ **Use Python 3.11 or 3.12 — not 3.13 or 3.14.**
> The backend uses `chromadb`, whose helper library only ships ready-made installers
> ("wheels") up to Python 3.12 on **Windows**. On 3.13/3.14, `pip` tries to compile
> from source and fails unless you've installed Microsoft's C++ build tools. Install
> **Python 3.11** and avoid the whole problem.

### 1.1 Install Python (3.11)

**Windows**
1. Download the "Windows installer (64-bit)" from
   <https://www.python.org/downloads/release/python-3119/>.
2. Run it. On the first screen **tick "Add python.exe to PATH"**, then "Install Now".
3. Reopen PowerShell and verify:
   ```powershell
   py -3.11 --version
   ```

**macOS**
```bash
brew install python@3.11   # or download the installer from python.org
python3.11 --version
```

**Linux (Debian/Ubuntu)**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
python3.11 --version
```

### 1.2 Install Node.js (18 or newer)

**Windows / macOS**
- Download the **LTS** installer from <https://nodejs.org/> and run it (defaults are
  fine). On macOS you can also use `brew install node`.

**Linux (Debian/Ubuntu)**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify (all platforms — reopen the terminal first):
```bash
node --version   # should be v18.x or higher
npm --version
```

### 1.3 Install Git (optional, only to clone)

Skip if you already have the `chat-with-pdf` folder.
- **Windows:** <https://git-scm.com/download/win>
- **macOS:** `brew install git` (or run `git --version` to trigger the installer)
- **Linux:** `sudo apt install -y git`

---

## 2. Get the project onto your computer

You most likely received this project as a **zip file** (`chat-with-pdf.zip`).
**Unzip it first:**

- **Windows:** right-click `chat-with-pdf.zip` → **Extract All…** → **Extract**. This
  creates a `chat-with-pdf` folder.
- **macOS:** double-click the zip in Finder; it extracts into a `chat-with-pdf` folder
  beside it.
- **Linux:** `unzip chat-with-pdf.zip` (install unzip first if needed:
  `sudo apt install -y unzip`).

> *Alternatively, if you were given a **Git URL** instead of a zip:*
> ```bash
> git clone <your-repo-url>
> ```

Open a terminal inside the extracted `chat-with-pdf` folder. You're in the right place
if you can see a `backend` folder and a `frontend` folder:
```bash
# Windows
dir
# macOS / Linux
ls
```

> **Note:** the zip intentionally does **not** include the Python virtual environment
> (`backend/venv`), the frontend's `node_modules`, API keys (`.env` files), or local
> data (`app.db`, `chroma_db/`). You create those in the steps below — that's normal
> and expected.

---

## 3. Get your Gemini API key

1. Go to <https://aistudio.google.com/apikey> and sign in with a Google account.
2. Click **"Create API key"**.
3. Copy the key — you'll paste it in Step 4.3. That's your `GEMINI_API_KEY`.

> The free tier works for trying the app but has daily/per-minute limits — see
> [Section 11](#11-notes-models-and-free-tier-limits).

---

## 4. Set up and run the BACKEND (Terminal #1)

Open a terminal and go into the `backend` folder:
```bash
cd backend
```
(You should now see `main.py`, `requirements.txt`, and a `.env.example` here.)

### 4.1 Create the virtual environment

**Windows (PowerShell):**
```powershell
py -3.11 -m venv venv
venv\Scripts\Activate.ps1
```
> If you get a red "running scripts is disabled" error, run this once and re-activate:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

**macOS / Linux:**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

Your prompt now shows `(venv)`. (Type `deactivate` to leave it later.)

### 4.2 Install the backend dependencies

```bash
pip install -r requirements.txt
```
This installs FastAPI, Uvicorn, ChromaDB, PyMuPDF, SQLAlchemy, the Gemini SDK, and
more. It can take a few minutes.

> **If it fails on `chroma-hnswlib` / `Microsoft Visual C++ 14.0` / "building wheel
> failed":** you're on Python 3.13/3.14. Delete the `venv` folder, install Python 3.11
> (Section 1.1), and redo Steps 4.1–4.2 with `py -3.11`/`python3.11`.

### 4.3 Configure the backend key (`.env`)

Copy the template to a real `.env` file and add your key:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
notepad .env
```
**macOS / Linux:**
```bash
cp .env.example .env
nano .env
```

Make it look like this (only `GEMINI_API_KEY` must change):
```
GEMINI_API_KEY=your-gemini-key
DATABASE_URL=sqlite+aiosqlite:///./app.db
CORS_ORIGINS=http://localhost:5173
```
Save and close.

> ⚠️ Put the key in **`.env`**, not `.env.example`. The backend only reads `.env`
> (which is git-ignored, so your key won't be committed).

### 4.4 Start the backend

```bash
uvicorn main:app --reload
```
Wait for:
```
... | INFO | main | Startup complete: database ready.
INFO:     Uvicorn running on http://127.0.0.1:8000
```
**Leave this terminal open.** Quick check: open <http://localhost:8000/health> in a
browser — you should see `{"status":"ok"}`.

---

## 5. Set up and run the FRONTEND (Terminal #2)

Open a **second** terminal (leave the backend running in the first one). Go to the
`frontend` folder from the project root:
```bash
cd chat-with-pdf/frontend
# or, if you're already in chat-with-pdf:  cd frontend
```

### 5.1 Install the frontend dependencies

```bash
npm install
```
(Downloads React, Vite, Tailwind, etc. into a `node_modules` folder. A few minutes.)

### 5.2 Configure the frontend (`.env`)

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```
**macOS / Linux:**
```bash
cp .env.example .env
```
The default contents already point at the backend, so you normally don't edit it:
```
VITE_API_URL=http://localhost:8000
```

### 5.3 Start the frontend

```bash
npm run dev
```
Wait for:
```
VITE v5.x  ready in ... ms
➜  Local:   http://localhost:5173/
```

---

## 6. Open the app

Open **<http://localhost:5173>** in your browser. You should see the **Chat with PDF**
interface (navy top bar, "Upload PDF" button) immediately — no login.

---

## 7. Verify it works

1. The page loads with an empty state ("Upload a PDF to get started").
2. Click **Upload PDF** and choose a text-based PDF (under 20 MB). It appears in the
   sidebar with a chunk count.
3. Type a question about the PDF and press Enter → the answer **streams in**, grounded
   in your document.
4. Ask something the document covers vs. something it doesn't — out-of-document
   questions are answered from general knowledge but **clearly labeled** as not from
   your documents.
5. Refresh the page → your document and chat history are still there (stored locally).
6. Open an **incognito window** → it's a fresh, empty session (different browser
   session = different data).
7. Delete a document (trash icon) or use **Reset session** to clear everything.

---

## 8. Everyday use (starting and stopping)

You need **both** terminals running. To start again later:

**Terminal #1 — backend:**
```bash
cd chat-with-pdf/backend
# activate venv:
#   Windows:        venv\Scripts\Activate.ps1
#   macOS / Linux:  source venv/bin/activate
uvicorn main:app --reload
```

**Terminal #2 — frontend:**
```bash
cd chat-with-pdf/frontend
npm run dev
```

Then open <http://localhost:5173>.

**To stop either one:** click its terminal and press **Ctrl + C**.

You only install dependencies once (Steps 4.2 and 5.1), not every time.

---

## 9. How your data is stored (good to know)

- **Documents & chat history** persist on the **backend** machine: an `app.db`
  (SQLite) file and a `chroma_db/` folder, both inside `backend/`. They survive
  restarts. Both are git-ignored.
- **Which data you see** is tied to a random **session id** stored in your browser's
  localStorage. Clear your browser data (or use a different browser/incognito) and you
  start fresh.

---

## 10. Troubleshooting

**Backend `pip install` fails: `chroma-hnswlib` / `Microsoft Visual C++ 14.0 required`
/ "building wheel failed"**
→ You're on Python 3.13/3.14. Use **Python 3.11**: delete `backend/venv`, recreate
with `py -3.11`/`python3.11`, reinstall.

**(Windows) `Activate.ps1 ... running scripts is disabled`**
→ Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.

**`python`/`py`/`node`/`npm` "not found"**
→ Reopen the terminal (PATH changes apply to new windows only). On macOS/Linux use
`python3.11`/`pip3`. On Windows, re-run the installer and ensure "Add to PATH".

**Backend won't start: `RuntimeError: Missing required environment variable GEMINI_API_KEY`**
→ The key isn't being read. Confirm `backend/.env` exists (exact name `.env`, not
`.env.txt`/`.env.example`) and contains `GEMINI_API_KEY=...`.

**The page loads but uploads/questions fail; browser console shows a CORS error**
→ The frontend and backend addresses must match. Backend `CORS_ORIGINS` must include
`http://localhost:5173` (the default) and the frontend `VITE_API_URL` must be
`http://localhost:8000` (the default). If you changed a port, update both and restart
both. **Restart the frontend after editing its `.env`** — Vite reads it at startup.

**Nothing happens / "connection refused" in the browser**
→ Make sure the **backend** terminal is still running and shows no errors, and that
<http://localhost:8000/health> returns `{"status":"ok"}`.

**`Port 8000` (or `5173`) `is already in use`**
→ Another process (maybe an old run) holds the port. Close it, or run on another port:
backend `uvicorn main:app --reload --port 8001` (then set `VITE_API_URL` to match);
frontend `npm run dev -- --port 5174` (then add that origin to backend `CORS_ORIGINS`).
To free a port on Windows: `Get-NetTCPConnection -LocalPort 8000 -State Listen` then
`Stop-Process -Id <PID> -Force`.

**Answers error with `Sorry, I ran into an error` or a "rate-limited / quota reached"
message**
→ Gemini free-tier quota. See [Section 11](#11-notes-models-and-free-tier-limits).
Wait for the daily reset or use a paid key.

**Backend terminal logs `404 ... model ... not found`**
→ The configured model name doesn't match your key's endpoint. This project is set to
`gemini-2.5-flash` / `gemini-embedding-001` in `backend/config.py`. If you changed them
to older names (e.g. `gemini-1.5-flash`), change them back.

**Styling looks wrong after editing `frontend/tailwind.config.js`**
→ Vite reads that config once at startup. Stop (`Ctrl+C`) and re-run `npm run dev`,
then hard-refresh the browser (Ctrl+Shift+R).

---

## 11. Notes: models and free-tier limits

- **Models used:** `gemini-2.5-flash` (chat answers) and `gemini-embedding-001` (PDF
  indexing), set in `backend/config.py`. These are the names that work with current
  Google AI Studio keys.
- **Free-tier limits (important):**
  - **Chat answers** are capped at roughly **20 requests per day** on the free tier.
    After that, questions show a "quota reached" message until the reset.
  - **Indexing (embeddings)** is limited to about **100 requests per minute**, so very
    large PDFs index slowly (the backend waits out the limit and continues).
  - **Daily limits reset at midnight US Pacific time.**
  - For real use, use a **paid Gemini API key**, or switch `GEMINI_MODEL` in
    `backend/config.py` to a model with a higher free daily limit (e.g.
    `gemini-2.0-flash`).
- **Never commit `.env`** files (backend or frontend) — they're git-ignored already.
