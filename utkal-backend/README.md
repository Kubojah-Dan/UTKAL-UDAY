## Utkal Backend (FastAPI)


- Unified question pipeline:
  - Existing local bank (`app/content/question_bank.json`)
  - Full XES3G5M ingestion (all 7,652 questions) including image-linked questions/analysis
  - Procedural generator (`GEN-*`) for Grades 1-12 in Mathematics, English, and Science
- KT-aware recommendations:
  - Uses interaction history + BKT mastery + DKT readiness signals
- Teacher XAI analytics:
  - Dependency graph inferred from prerequisite routes
  - Root-cause skill table
  - Prerequisite GPA gap analysis
  - Causal chain extraction
- Daily trend fix:
  - Rolling date window with zero-filled days.
- Static image serving for XES:
  - `GET /xes-images/{filename}`
- Dataset inspection endpoint:
  - `GET /datasets/xes3g5m/inspect`

### Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Train XES3G5M Models (DKT + BKT)

Run from `utkal-backend`:

```bash
py -m app.scripts.train_xes_models --epochs 10 --batch-size 128 --lr 8e-4 --val-fold 4
```

Artifacts are written to `app/models`:

- `app/models/dkt_xes3g5m.pt`
- `app/models/dkt_xes3g5m_meta.json`
- `app/models/bkt_params_xes3g5m.json`
- `app/models/xes_training_report.json`

### Model Artifact Deployment Workflow

The backend expects a few large model files at runtime, but these should not be committed to Git if they exceed GitHub limits.

1. Host model artifacts externally using one of these options:
   - GitHub Releases
   - AWS S3 / Google Cloud Storage / Firebase Storage
   - A private blob store or artifact bucket

2. Expose a base URL for downloads, for example:

```bash
UTKAL_MODEL_BASE_URL=https://storage.googleapis.com/your-bucket/models
```

3. Enable auto-download when the backend starts:

```bash
UTKAL_MODEL_DOWNLOAD_ENABLED=true
```

4. The backend will download any missing files into `app/models/` before it begins serving requests.

5. Use the helper script locally to fetch artifacts manually:

```bash
python scripts/fetch_models.py
```

### Expected Runtime Artifacts

At minimum the backend should have:

- `app/models/quest2skill.json`
- `app/models/dkt_xes3g5m.pt`
- `app/models/temporal_lstm.pt`

If you want full DKT/BKT behavior also include:

- `app/models/dkt_xes3g5m_meta.json`
- `app/models/bkt_params_xes3g5m.json`

### Key Endpoints

- `POST /auth/login`
- `GET /auth/me`
- `GET /subjects`
- `GET /questions?subject=&grade=&offset=&limit=&include_generated=`
- `GET /questions/{question_id}`
- `GET /datasets/xes3g5m/inspect`
- `GET /recommend/{student_id}`
- `POST /sync`
- `GET /teacher/analytics`
- `GET /teacher/student/{student_id}`
- `GET /models/readiness`
- `GET /bkt/latest`

### Env Vars

- `UTKAL_TEACHER_PASSWORD` (default: `teacher123`)
- `UTKAL_AUTH_SECRET`
- `UTKAL_SYNC_KEY`
- `UTKAL_RATE_LIMIT`
- `UTKAL_RATE_WINDOW`
- `UTKAL_STARTUP_LOCALIZATION_ENABLED` (default: `false`)
- `UTKAL_STARTUP_LOCALIZATION_LANGUAGES` (default: `hi,ta,te,or`)
- `UTKAL_STARTUP_LOCALIZATION_DELAY_SECONDS` (default: `10`)
- `UTKAL_STARTUP_LOCALIZATION_MAX_QUESTIONS` (default: `12`)
- `UTKAL_MODEL_DOWNLOAD_ENABLED` (default: `false`)
- `UTKAL_MODEL_BASE_URL` (required when download enabled)
- `UTKAL_MODEL_FILES` (optional JSON list of artifact filenames)

### Localization Behavior

- Startup no longer blocks the API by translating questions immediately.
- Missing non-English variants are queued on demand when questions are fetched.
- If you want a gentle warm-up after boot, enable `UTKAL_STARTUP_LOCALIZATION_ENABLED=true`.

### Automatic Web Question Intake (Recommended Workflow)

1. Source only open-license banks (OER/Common-Core aligned content).
2. Normalize each question into this schema:
   - `id`, `subject`, `grade`, `skill_id`, `skill_label`, `type`, `question`, `options`, `answer`, `hint`, `explanation`
3. Run quality filters:
   - deduplicate by normalized text hash
   - enforce grade/subject tagging
   - reject malformed options/answers
4. Append to your ingestion file and expose via `app/core/question_bank.py`.
5. Re-train KT artifacts (`train_xes_models.py`) periodically.

You can automate steps 1-4 with a scheduled scraper + validation pipeline, then push cleaned items into your question ingestion layer.
