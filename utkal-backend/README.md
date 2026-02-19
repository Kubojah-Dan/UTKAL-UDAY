## Utkal Backend (FastAPI)

### Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Key Endpoints

- `POST /auth/login`
- `GET /auth/me`
- `GET /questions`
- `GET /questions/{question_id}`
- `GET /recommend/{student_id}`
- `POST /sync`
- `GET /teacher/analytics`
- `GET /models/readiness`

### Env Vars

- `UTKAL_TEACHER_PASSWORD` (default: `teacher123`)
- `UTKAL_AUTH_SECRET`
- `UTKAL_SYNC_KEY`
- `UTKAL_RATE_LIMIT`
- `UTKAL_RATE_WINDOW`

### Content

Starter Math + Science questions are in:

- `app/content/question_bank.json`
