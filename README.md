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

## ✨ All Features (Complete List)

### 🎓 Student Experience
- **Interactive Quests** — MCQ, fill-in-blank, descriptive, image-based questions
- **AI Recommendations** — KT/BKT/DKT-powered personalized quest paths
- **Prerequisite Graph** — Never recommends advanced topics before basics
- **Question Timer** — Countdown based on difficulty (60/90/120 seconds)
- **Celebration Animation** — Full-screen sparkles on perfect answers
- **Daily Streak** — Fire icon, streak count, bonus XP for consecutive days
- **Daily Challenge** — One hard question per day with +50 bonus XP
- **SM-2 Spaced Repetition** — Schedules question reviews for long-term retention
- **Offline Download** — Pre-download 600 questions for offline use
- **Multi-Language** — Tamil, Hindi, Telugu, Odia, English (instant, no API call)
- **Achievement Badges** — 11 badges across accuracy, speed, streaks, subjects
- **XP & Levels** — 120 XP per level, progress bar, level-up tracking
- **Leaderboard** — Compete with classmates (same school or all schools, same grade)
- **Quiz System** — Timed assessments with instant results

### 👩‍🏫 Teacher Experience
- **Secure Registration** — Email + password with teacher registration code
- **AI Question Generation** — Generate NCERT-aligned questions by topic/grade/subject
- **PDF Upload** — Upload documents, AI extracts questions automatically
- **Approval Workflow** — Review, translate, and approve questions before publishing
- **Skill Heatmap** — Visual grid of topic accuracy across the class
- **At-Risk Alerts** — Automatic detection of struggling students (accuracy < 40%)
- **Subject Radar Chart** — Class strengths/weaknesses by subject
- **Dependency Graph** — XAI prerequisite chains and risk levels
- **Daily Trend Chart** — Attempts and accuracy over time
- **Quiz Analytics** — Track quiz attempts and average scores

### 🔐 Security & Auth
- **Email + Password** — Proper authentication for all users
- **PBKDF2-HMAC-SHA256** — Production-grade password hashing
- **JWT Tokens** — 7-day session tokens
- **Role-Based Access** — Student/Teacher routes strictly separated
- **Teacher Code** — Secret registration code prevents unauthorized teacher accounts

---

## 🗂️ File Reference

### New Backend Files
| File | Purpose |
|------|---------|
| `app/api/student.py` | Streak, daily challenge, spaced repetition, leaderboard, offline download endpoints |
| `app/core/streak_service.py` | Daily streak tracking logic |
| `app/core/spaced_repetition.py` | SM-2 algorithm implementation |
| `app/core/leaderboard_service.py` | Leaderboard MongoDB queries |
| `fix_all_translations.py` | Fix untranslated/incomplete questions (run once) |
| `full_diagnostic.py` | Check translation status across all questions |

### Modified Backend Files
| File | Change |
|------|--------|
| `app/api/auth.py` | Full rewrite — email+password register/login |
| `app/core/auth.py` | Added `hash_password()`, `verify_password()` |
| `app/core/groq_translator.py` | Rate limit retry, removed unicode chars |
| `app/api/recommend.py` | Fixed grade filter, added prerequisite graph |
| `app/api/sync.py` | Auto-updates streak + leaderboard on sync |
| `app/main.py` | Added student router, startup auto-translation |
| `app/generators/math_generator.py` | Expanded to grades 1-12, all topics |

### Modified Frontend Files
| File | Change |
|------|--------|
| `src/pages/Login.jsx` | Full rewrite — split-panel sliding design |
| `src/pages/Home.jsx` | Added streak bar, daily challenge, offline download |
| `src/pages/Quest.jsx` | Added timer, celebration, spaced repetition update |
| `src/pages/Progress.jsx` | Full rewrite — added leaderboard section |
| `src/pages/TeacherDashboard.jsx` | Added heatmap, at-risk alerts, radar chart |
| `src/components/Header.jsx` | Fixed mobile nav, Get Started → register |
| `src/services/auth.js` | Updated for email+password register/login |
| `src/context/LanguageContext.jsx` | Removed debug console.log statements |
| `src/index.css` | Added auth page, leaderboard, heatmap, timer, streak, celebration CSS |

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS + custom CSS
- **State/Data**: Axios, Dexie (IndexedDB), PouchDB
- **Visualization**: Recharts (Line, Bar, Radar charts), Lucide Icons
- **Mobile**: Capacitor (Android support), PWA

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB (via Motor async + PyMongo sync)
- **AI/ML**: PyTorch (DKT), Scikit-learn, NumPy, Pandas
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



