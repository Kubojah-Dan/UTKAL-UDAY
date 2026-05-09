# Utkal Uday

Utkal Uday is a comprehensive educational platform designed to empower students through procedural quest-based learning and provide teachers with advanced AI-driven analytics. The system integrates a modern React frontend with a robust FastAPI backend, featuring Knowledge Tracing (KT) and Explainable AI (XAI) for personalized education.

**🎯 Built for rural Indian students (Grades 1-12) with multi-language support including Tamil, Hindi, Telugu, and Odia.**

---

## 🚀 Quick Start

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

Or manually:
```bash
# Backend
cd utkal-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd utkal-frontend
npm install
npm run dev
# Seed Initial Content (Science/EVS/Social Science)
# (In backend directory)
python scripts/seed_content.py
```

---

## 🔑 Environment Configuration

### Backend (`utkal-backend/.env`)
```env
GROQ_API_KEY
MONGODB_URL
UTKAL_TEACHER_PASSWORD
UTKAL_AUTH_SECRET
```

**Get API Keys:**
- **Groq API**: https://console.groq.com/keys (Free tier: 30 requests/minute)

### Frontend (`utkal-frontend/.env`)
```env
VITE_API_BASE
VITE_ANDROID_API_BASE
```

---

## 🌟 Major Highlights

- **Vision-Powered PDF Parsing** — Upload complex PDFs with diagrams and formulas; Llama 3.2 Vision extracts questions with 99% accuracy.
- **Procedural Question Generators** — Infinite questions for Mathematics (Trig, Calculus), Science (Grades 1-10), and Social Science (Civics, Geography).
- **Offline-First Sync Engine** — Every action is queued in IndexedDB; syncs automatically when online.
- **Study Notes & Concept Cards** — Swipeable content cards with **Offline Text-to-Speech (TTS)** support.
- **Explainable AI (XAI)** — Prerequisite dependency graphs and "Root Cause" skill analysis for teachers.
- **Spaced Repetition (SM-2)** — Personalized review schedules to combat the forgetting curve.
- **Conflict Resolution** — "Higher XP Wins" strategy for cross-device consistency.
- **Sync Status Pills** — Real-time indicators showing pending/offline/online states.
- **Automated Certificates** — PDF merit certificates for top-ranking students.
- **Hall of Fame** — Permanent recognition for seasonal leaderboard winners.
- **Quiz System** — Timed assessments with instant results and teacher analytics.

---

## 🚀 Quick Start

```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

Or manually:
```bash
# Backend
cd utkal-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd utkal-frontend
npm install
npm run dev

# Seed Initial Content (Bulk Admin Tool)
# 1. Login as teacher
# 2. Go to Teacher Dashboard -> Content Management
# 3. Use 'Bulk Database Seeder' at the bottom
```

---

## 👩‍🏫 Teacher Experience

- **Vision AI Document Parsing** — Upload PDFs; AI "sees" diagrams and recreates them as responsive SVGs.
- **Bulk Database Seeding** — One-click generation of 20+ questions per subject/grade.
- **Skill Heatmap** — Visual grid of topic accuracy across the class.
- **At-Risk Alerts** — Automatic detection of struggling students (accuracy < 40%).
- **Subject Radar Chart** — Class strengths/weaknesses by subject.
- **Dependency Graph** — XAI prerequisite chains and risk levels.
- **Quiz Analytics** — Track quiz attempts, average scores, and absent students.

---

## 🔄 Automation & Deployment

### Nightly Batch Generation
The system supports automated question generation. In production, set up a **Cron Job** (or Cloud Scheduler) to trigger the admin endpoint:

```bash
# Example Cron Command (runs at 2 AM daily)
0 2 * * * curl -X POST "https://your-api.com/admin/generate-batch" -H "Authorization: Bearer <TOKEN>"
```

### Local Manual Seeding
You can also run the generation script manually from the terminal:
```bash
cd utkal-backend
python -m scripts.nightly_batch_generate
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS + Premium Vanilla CSS
- **State/Data**: Axios, Dexie v3 (Sync Queue), PouchDB
- **Offline**: Service Workers + Background Sync API + Web Speech API (TTS)
- **Visualization**: Recharts (Line, Bar, Radar charts), Lucide Icons
- **PDF Generation**: fpdf2

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB (via Motor async)
- **AI/ML**: PyTorch (DKT), Scikit-learn, Llama 3.2 Vision (via Groq)
- **Translation**: Groq API (Llama 3.1 8B Instant)
- **Graph Logic**: NetworkX, Pgmpy
- **Server**: Uvicorn


### MongoDB Collections
| Collection | Purpose |
|-----------|---------|
| `questions` | All questions with translations |
| `users` | Registered users (email + hashed password) |
| `student_leaderboard` | XP/level/badges per student for leaderboard |
| `student_streaks` | Daily streak tracking |
| `daily_challenges` | Today's challenge per grade |
| `spaced_reviews` | SM-2 review schedules per student |
| `quizzes` | Teacher-created quizzes |
| `student_attempts` | Quiz attempt records |

---

## 🔄 Translation Management

### Check Status
```bash
cd utkal-backend
python full_diagnostic.py
```

### Fix Untranslated Questions
```bash
python fix_all_translations.py
```
- Processes one question at a time with 3s delay between languages
- Handles 429 rate limit errors with automatic retry
- Takes ~14 seconds per question (4 languages × 3s + 2s gap)

### Translation Architecture
```
Teacher approves question → Groq API translates to hi/ta/te/or
→ Saved to MongoDB with language_variants field
→ Student selects language → instant display (no API call)
```

---

## 📱 Mobile Support

### Responsive Breakpoints
- **> 768px**: Full desktop navigation
- **< 768px**: Hamburger menu, stacked layouts, touch-friendly targets

### Android App
```bash
cd utkal-frontend
npm run build
npx cap sync
npx cap open android
```

---

## 🧬 AI & Models

### Knowledge Tracing
```bash
# Train DKT and BKT models
py -m app.scripts.train_xes_models --epochs 10 --batch-size 128
```
Artifacts stored in `utkal-backend/app/models/`.

### Question Generation
- **Procedural**: Unlimited math questions via `app/generators/math_generator.py`
- **AI-Generated**: Groq API generates conceptual questions via teacher dashboard
- **PDF Upload**: AI extracts questions from uploaded documents



