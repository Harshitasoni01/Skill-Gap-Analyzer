# SkillGap — Resume Skill Gap Analyzer

Upload a resume and a job description. The AI reads both and tells you:

- **Matching skills** — what the resume already covers
- **Missing skills** — what the job needs but the resume does not show
- **Match score (0–100)** with a short explanation

This is a focused version of the HireMind AI recruiting system: the same resume parsing, AI extraction and AI matching, with only the skill-gap feature and a plain HTML/CSS/JS frontend.

---

## Tech stack

| Part | Technology |
|---|---|
| Backend | Python, FastAPI |
| Resume parsing | PyMuPDF (PDF), python-docx (DOCX) |
| AI | Google Gemini 2.5 Flash (`google-genai` SDK) |
| Frontend | HTML, CSS, JavaScript (no framework) |

There is no database. Every analysis is one request and one response, and nothing is stored.

---

## How to run (Windows)

You need Python 3.10 or newer and a free Gemini API key from https://aistudio.google.com/apikey

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `backend/.env` and put your key in:

```
GEMINI_API_KEY=your_real_key_here
```

Start the server:

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** in your browser. The same server serves the website and the API.

(Mac/Linux: use `source venv/bin/activate` and `cp .env.example .env`.)

Interactive API docs are at http://127.0.0.1:8000/docs

---

## Project structure

```
skill-gap-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py                    # creates the app, CORS, serves the frontend
│   │   ├── schemas.py                 # shape of the API response
│   │   ├── routes/
│   │   │   └── analyze_routes.py      # POST /api/analyze
│   │   ├── services/
│   │   │   ├── resume_parser.py       # PDF / DOCX / TXT  ->  plain text
│   │   │   ├── gemini_client.py       # one function that calls Gemini (with retries)
│   │   │   ├── analyzer.py            # runs agent 1, then agent 2
│   │   │   └── utils.py               # safe JSON parsing and cleanup helpers
│   │   └── agents/
│   │       ├── extraction_agent.py    # resume text  ->  structured profile
│   │       └── matching_agent.py      # profile + job  ->  score, matched, missing
│   ├── requirements.txt
│   ├── .env.example
│   └── Procfile                       # for deploying on Render
└── frontend/
    ├── index.html                     # page structure
    ├── style.css                      # dark theme and layout
    ├── script.js                      # upload, API call, rendering results
    └── config.js                      # backend URL
```

---

## How it works

```
Browser (HTML/CSS/JS)
   |  POST /api/analyze   (resume file + job description)
   v
FastAPI route ---------- validates files (type, size, not empty)
   v
resume_parser ---------- PDF/DOCX  ->  plain text
   v
Agent 1: extraction ---- Gemini turns resume text into JSON:
                         name, skills, experience, projects, education, companies
   v
Agent 2: matching ------ Gemini compares that profile + the raw resume text
                         with the job description and returns JSON:
                         match_score, matched_skills, missing_skills, reasons
   v
Response JSON ---------- the browser draws the score ring and skill chips
```

### API

`POST /api/analyze` (multipart form data)

| Field | Required | Notes |
|---|---|---|
| `resume` | yes | PDF or DOCX, max 5 MB |
| `jd_text` | one of these two | pasted job description (at least 40 characters) |
| `jd_file` | one of these two | PDF, DOCX or TXT. Ignored if `jd_text` is sent |

Example response:

```json
{
  "candidate_name": "Pratham Parmar",
  "resume_skills": ["Python", "FastAPI", "Docker"],
  "match_score": 72,
  "verdict": "Partial match",
  "matched_skills": ["Python", "Docker"],
  "missing_skills": ["Django", "AWS"],
  "reasons": ["...", "...", "..."]
}
```

Verdict: 75+ is "Strong match", 50–74 is "Partial match", below 50 is "Weak match".

---

## How to explain this project

**One-minute pitch**

> Job seekers often don't know why their resume gets rejected. This tool takes a resume and a job description and shows the skill gap: which required skills the resume covers, which are missing, and a match score with reasons. The backend is FastAPI. It extracts text from the PDF or DOCX, then uses two Gemini AI steps: the first turns the resume into a structured profile, the second compares that profile and the resume text against the job description. The frontend is plain HTML, CSS and JavaScript.

**Why two AI steps instead of one?**
Each step does one job and can be checked on its own. Step 1 only reads, step 2 only judges. If the result looks wrong, you can look at the extracted profile and see which step went wrong.

**Why does the matching step also get the raw resume text?**
A skills list is only keywords. The full text shows how deep the work was, for example "built 20 production APIs" versus just listing "REST APIs". The AI is told to judge real depth, not keyword overlap.

**How do you make sure the AI answer can be used by code?**
The prompt asks for JSON in a fixed shape. Models sometimes still add text or ```` ```json ```` fences, so `utils.py` cuts out the part between the first `{` and the last `}` before parsing. Then every field is cleaned: the score is forced to an integer from 0 to 100, lists are de-duplicated, and wrong types become empty lists. If the answer cannot be parsed at all, the user gets a clear error instead of a made-up result.

**What happens when the AI service is busy or rate-limited?**
`gemini_client.py` retries temporary errors (429 and 503) up to 3 times with a short wait. A per-day quota error is not retried, because waiting seconds cannot fix it. The user gets a readable message.

**Why `run_in_threadpool` in the route?**
The Gemini call is slow and blocking. Running it in a worker thread keeps the server responsive to other requests.

**Why no database?**
The feature is a single request and response. Nothing needs to be saved, so a database would only add complexity.

**Why `textContent` and not `innerHTML` in the frontend?**
The skill names come from an AI. Using `textContent` means that text can never be treated as HTML, so it cannot inject scripts into the page.

**What does the loading text do?**
The server does everything in one request, so the changing messages ("Reading your resume...", "Comparing...") are a visual hint only. They are not real-time progress.

---

## Known limitations (be honest about these)

- **Scanned PDFs** (images of text) cannot be read. There is no OCR. The app tells the user to upload a text-based PDF or a DOCX.
- **DOCX tables and text boxes** are not read, only normal paragraphs.
- **The score comes from an AI model**, so the same input can give a slightly different score on another run. It is guidance, not an exact measurement.
- **Free Gemini quota is small.** Each analysis uses 2 AI calls.
- **No login and no storage.** Anyone with the link can use it, and results are not saved.

## Possible improvements

- OCR for scanned resumes
- Suggestions for how to learn or show each missing skill
- Saving past analyses (add a database)
- Comparing one resume against several jobs

---

## Deploying (optional)

**Backend (Render):** root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add environment variables `GEMINI_API_KEY` and `ALLOWED_ORIGINS` (your frontend URL).

**Frontend (Vercel/Netlify):** deploy the `frontend` folder as a static site, after changing `API_BASE_URL` in `frontend/config.js` to your Render URL.
