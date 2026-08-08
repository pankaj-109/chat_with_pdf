# Chat with PDF

A full-stack web app that lets you upload PDF documents and chat with an AI about
them. It retrieves the most relevant passages with a vector search and streams a
grounded answer back token by token. When your documents don't contain the answer,
the bot falls back to general knowledge but **clearly labels** that reply as not
coming from your documents, so grounded and general answers stay distinguishable.
There is no login — each browser gets an anonymous session, and your documents and
chat history are scoped to that session.

> 🛠️ **New here? Read [SETUP.md](SETUP.md)** — a step-by-step, beginner-friendly
> guide to setting this up on a fresh machine (installing Python & Node, getting your
> Gemini key, running the backend + frontend) for Windows, macOS, and Linux. The
> Setup section below is the condensed version.

## Screenshots

<!-- TODO: add screenshots -->

## Architecture

```
                          ┌───────────────────────────── Browser (React + Vite) ─────────────────────────────┐
                          │  Sidebar (upload / docs / reset)   Chat area (streamed answers)   Top bar         │
                          │  - session UUID in localStorage, sent as X-Session-Id on every request             │
                          └───────────────┬───────────────────────────────────────────────────────────────────┘
                                          │  HTTP + Server-Sent Events (SSE)
                                          ▼
                          ┌───────────────────────── FastAPI (Uvicorn, async) ──────────────────────────┐
                          │  /api/documents   /api/chat (SSE)   /api/chat/history   /api/session          │
                          │                                                                               │
                          │   ┌─────────────┐     ┌──────────────┐     ┌─────────────────────────────┐    │
                          │   │  PyMuPDF    │     │   ChromaDB   │     │           Gemini            │    │
                          │   │ extract +   │     │ per-session  │     │ gemini-embedding-001 (embed)│    │
                          │   │ chunk text  │     │ vector store │     │ gemini-2.5-flash (generate) │    │
                          │   └─────────────┘     └──────────────┘     └─────────────────────────────┘    │
                          │                                                                               │
                          │   SQLite (via SQLAlchemy async + aiosqlite): documents + message history       │
                          └───────────────────────────────────────────────────────────────────────────────┘
```

Data flow for a question: embed the question → retrieve top-K chunks from the
session's Chroma collection → build a strictly-grounded prompt (retrieved chunks +
recent history) → stream Gemini's answer back over SSE → persist both messages to
SQLite.

## Setup

You need **Python 3.10–3.12** (see note below), **Node 18+**, and a **Gemini API key**.

> ⚠️ **Python version on Windows.** `chromadb` depends on `chroma-hnswlib`, which
> only ships prebuilt Windows wheels up to Python 3.12. On 3.13 / 3.14 `pip` tries
> to compile from source and fails without the MS Visual C++ Build Tools. Use
> Python **3.11** or **3.12**.

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd chat-with-pdf
   ```

2. **Get a Gemini API key** from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

3. **Backend**
   ```bash
   cd backend
   python -m venv venv          # on Windows, prefer: py -3.11 -m venv venv
   source venv/bin/activate     # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env         # then edit .env and paste your GEMINI_API_KEY
   uvicorn main:app --reload
   ```
   The API starts on `http://localhost:8000`.

4. **Frontend** (in a second terminal)
   ```bash
   cd frontend
   npm install
   cp .env.example .env         # default points at http://localhost:8000
   npm run dev
   ```

5. Open **`http://localhost:5173`**.

## Usage

- **Upload a PDF** from the sidebar — it's extracted, chunked, embedded, and indexed
  into your session's vector store. The sidebar shows each document and its chunk count.
- **Ask a question** in the chat box. The answer streams back and is grounded strictly
  in your uploaded documents. If the answer isn't in them, the bot says so rather than
  guessing.
- **Follow-up questions** work — the last few exchanges are included as context.
- **Delete a document** (trash icon) to remove it from retrieval, or **Clear
  conversation** to wipe just the chat.
- **Reset session** deletes everything (documents + history) and starts a brand-new
  anonymous session.
- Your session lives in `localStorage`, so a **refresh keeps your state**; an
  **incognito window** is a different session and starts empty.

## Project structure

```
chat-with-pdf/
├── README.md
├── .gitignore
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app, CORS, route registration
│   ├── config.py               # env vars + constants
│   ├── database.py             # SQLAlchemy async engine + session
│   ├── models.py               # SQLAlchemy models: Document, Message
│   ├── schemas.py              # Pydantic request/response models
│   ├── dependencies.py         # FastAPI dependency: get_session_id from header
│   ├── routes/
│   │   ├── documents.py        # CRUD for the session's documents
│   │   ├── chat.py             # POST /api/chat (streaming SSE) + history
│   │   └── session.py          # DELETE /api/session (clear everything)
│   └── rag/
│       ├── pdf_processor.py    # extract_text, chunk_text
│       ├── embeddings.py       # Gemini embeddings wrapper
│       ├── vector_store.py     # ChromaDB wrapper
│       └── generator.py        # Gemini streaming generator
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx            # entry
        ├── App.tsx             # main layout + state
        ├── index.css           # tailwind directives
        ├── types.ts            # shared TypeScript types
        ├── session.ts          # getOrCreateSessionId(), resetSession()
        ├── api/                # client.ts, documents.ts, chat.ts (SSE)
        └── components/         # Sidebar, ChatArea, Message, ... (UI)
```

## Note on model names

The original spec named `gemini-1.5-flash` and `text-embedding-004`. Those models
return **HTTP 404** on the current Gemini API endpoint used by newer API keys, so
this project uses the working equivalents — `gemini-2.5-flash` and
`gemini-embedding-001` — configured in `backend/config.py`. Change them there if your
key supports the originals.

## Known limitations

- **Anonymous, session-based** — there are no user accounts. Your data is tied to a
  UUID in `localStorage`; clear your browser data and you lose access to it.
- **Single-server** — SQLite + a local ChromaDB directory. No horizontal scaling.
- **No rate limiting** and no abuse protection.
- **Free-tier Gemini quota** — the free tier is the main practical limit. Chat
  generation (`gemini-2.5-flash`) is capped at roughly **20 requests per day**, after
  which questions return a "rate-limited / quota reached" notice until the daily reset.
  Embeddings are limited to ~100 requests/minute, so very large PDFs index slowly (the
  backend waits out the window). For real use, use a **paid API key** — or switch
  `GEMINI_MODEL` in `backend/config.py` to a model with a higher free-tier daily limit
  (e.g. `gemini-2.0-flash`).
- **Text-based PDFs only** — no OCR, so scanned/image-only PDFs yield no text.

## License

MIT
