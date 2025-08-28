 🧠 HealthFact AI

HealthFact AI is a fact-checking and learning platform designed to fight health misinformation.  
Users can check claims, play quizzes, and learn simple tips for spotting false health advice.  

---

🚀 Features

 ✅ Core Features (MVP)
- **Claim Checker**  
  - Input a health claim → get verdict (`True/False`) + explanation + trusted source.  
  - Uses FastAPI backend, NLP rules (spaCy + regex), and limited web scraping.

- **Quiz / Game Mode**  
  - 5–10 quiz questions per session.  
  - Tracks score locally.  
  - Shows learning tips after each answer.

- **Learning Tips (MIL Framework)**  
  - Short, practical cards after fact-check/quiz.  
  - Example: “Always check if the claim links to WHO or CDC.”

 ⏳ Advanced (Future)
- User login + progress tracking  
- Dashboard with charts (progress over time)  
- Admin panel to add/update misinformation claims  
- Multilingual support (English/Hindi)  
- AI-powered classification (Hugging Face Transformers)

---

 🛠️ Tech Stack

- **FastAPI** → API backend (fast, auto-docs, async support)  
- **Streamlit** → UI for claim checker, quiz, dashboard  
- **SQLite** → lightweight DB for claims + quiz bank  
- **spaCy + Regex** → language processing & pattern matching  
- **Requests + BeautifulSoup4** → scrape trusted sources (WHO, CDC, etc.)  
- *(Later: Django + PostgreSQL for advanced features)*  

---
📜 License

MIT License © 2025 HealthFact AI Team

---

## Getting Started

### 3) Run the server

## Team Setup with Doppler

Teammates:
1. Install Doppler CLI; `doppler login`.
2. You add them to project `healthfactai` (config `dev`).
3. In repo: `doppler setup --project healthfactai --config dev`
4. Run: `doppler run -- uvicorn main:app --reload`
- With Doppler:

```powershell
doppler run -- uvicorn main:app --reload
```

Restart note: after changing `.env`/secrets, stop (Ctrl+C) and start again.

## API Overview

- Swagger: `http://127.0.0.1:8000/docs`

### Auth
- POST `/register/` (query params `username`, `password`)
- POST `/token` (form fields `username`, `password`) → returns `access_token`
- GET `/me` (Bearer auth)

### Verified Search
- POST `/search_verified`
  - Body: `{ "claim": "...", "top_urls": 6, "passages_per_url": 3 }`
  - Returns allow-listed sources with ranked passages

### Quiz
- POST `/quiz_from_claim`
  - Body: `{ "claim": "...", "num_questions": 5, "difficulty": "mixed", "style": "conceptual" }`
  - Requires `OPENAI_API_KEY`. Generates MCQs strictly from verified snippets
- POST `/grade_quiz`
  - Body: `{ "answers": [...], "key": [...] }` → returns score

### Health
- GET `/healthz` → `{ "status": "ok" }`

## Troubleshooting

- Readability/lxml clean error: install extra

```powershell
pip install --no-cache-dir "lxml[html_clean]==5.3.0"
```

- OpenAI proxy issues: do not set `OPENAI_*PROXY`. If needed, use standard `HTTPS_PROXY` env var.
