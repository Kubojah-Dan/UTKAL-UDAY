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
GROQ_API_KEY=your_groq_api_key_here
MONGODB_URL=mongodb://localhost:27017/utkal_uday
UTKAL_TEACHER_PASSWORD=teacher_registration_code
UTKAL_AUTH_SECRET=your_jwt_secret_here
```

**Get API Keys:**
- **Groq API**: https://console.groq.com/keys (Free tier: 30 requests/minute)

### Frontend (`utkal-frontend/.env`)
```env
VITE_API_BASE=http://127.0.0.1:8000
VITE_ANDROID_API_BASE=http://10.0.2.2:8000
```

---

## 📋 Updates (Session Log)

### 🔐 1. Authentication — Proper Register + Login System

**Problem:** The old system had no real authentication — students just typed their name and teachers used a hardcoded password `teacher123`. Not suitable for production.

**Solution:** Full email + password authentication with secure password hashing.

#### Backend 
- **`app/api/auth.py`** — Replaced name-based login with:
  - `POST /auth/register` — Creates user in MongoDB `users` collection with hashed password
  - `POST /auth/login` — Verifies email + password, returns JWT token
- **`app/core/auth.py`** — Added `hash_password()` and `verify_password()` using **PBKDF2-HMAC-SHA256** (260,000 iterations + random salt)

#### Frontend 
- **`src/pages/Login.jsx`** — Completely rebuilt as a **split-panel sliding design**:
  - Desktop: animated overlay panel slides between Sign In and Sign Up
  - Mobile: simple toggle with "Already have an account?" links
  - Password show/hide toggle on all password fields
  - Role toggle (Student / Teacher) on register form
  - Teacher registration requires a `Teacher Registration Code` (set via `UTKAL_TEACHER_PASSWORD` env var)
- **`src/services/auth.js`** — Updated to call `/auth/register` and `/auth/login` with email/password
- **`src/components/Header.jsx`** — "Get Started" → opens Register panel; "Login" → opens Sign In panel

#### How It Works
```
Register:  email + password + name + school + grade → hashed in MongoDB → JWT token
Login:     email + password → verify hash → JWT token → access platform
Teacher:   same flow + teacher_code (secret registration code from .env)
```

#### Security Notes
- Passwords stored as PBKDF2 hashes, never plaintext
- JWT tokens unchanged — all existing sessions continue working
- Role-based access enforced by `ProtectedRoute` (frontend) and `get_current_user` (backend)
- Teacher code is set via env var, not hardcoded

---

### 🌐 2. Translation System — Rate Limit Fix & Auto-Translation

**Problem:** Groq API returns 429 (Too Many Requests) when translating many questions at once. Unicode characters in print statements caused `UnicodeEncodeError` on Windows.

#### Backend Changes
- **`app/core/groq_translator.py`** — Completely rewritten:
  - Removed all unicode emoji characters (`✓`, `✗`, `📊`) that broke Windows cp1252 encoding
  - Added automatic retry with exponential backoff on 429 errors (waits 60s, 120s, 180s, 240s)
- **`fix_all_translations.py`** — Rewritten to process one question at a time with 3-second delay between language calls (stays safely under 30 req/min free tier limit)
- **`app/main.py`** — Added `@app.on_event("startup")` background task that auto-translates up to 50 untranslated questions every time the server starts

#### Translation Scripts
```bash
# Fix all untranslated/incomplete questions (run once)
cd utkal-backend
python fix_all_translations.py

# Check translation status
python full_diagnostic.py
```

---

### 📱 3. Mobile Navigation — Final Fix

**Problem:** Desktop nav was still showing on mobile alongside the hamburger menu. CSS classes were conflicting.

#### Frontend Changes
- **`src/components/Header.jsx`** — Added `desktop-nav` and `desktop-actions` CSS classes to desktop elements
- **`src/index.css`** — Replaced broken mobile CSS with clean implementation:
  - `desktop-nav` and `desktop-actions` hidden with `display: none !important` on mobile
  - Hamburger button uses `display: flex` on mobile
  - Removed conflicting 920px/640px media queries
  - Proper touch targets (14px padding on nav items)
  - Mobile menu has backdrop blur, border-top, and slideDown animation

#### Behavior
| Screen | Navigation |
|--------|-----------|
| > 768px | Traditional horizontal nav bar |
| < 768px | Hamburger icon (☰), full-screen overlay menu |

---

### 🎉 4. Celebration Animation

**Problem:** No visual feedback when students answer correctly.

#### Frontend Changes
- **`src/pages/Quest.jsx`** — Added `showCelebration` state, triggers on correct answer with no hints used
- **`src/index.css`** — Added `.celebration-overlay` with:
  - Full-screen teal overlay
  - Spinning gold Sparkles icon
  - "🎉 Perfect! Full XP Earned!" text
  - Fade in/out over 5 seconds, auto-disappears

---

### 🔥 5. Streak System

**Problem:** No daily engagement hooks to bring students back.

#### Backend Changes
- **`app/core/streak_service.py`** — New service:
  - `update_streak(student_id)` — tracks daily streaks, longest streak, total active days
  - `get_or_create_streak(student_id)` — fetches or initializes streak document
  - Bonus XP: 5 XP × streak days (max 50 XP)
- **`app/api/student.py`** — Endpoints:
  - `GET /student/streak/{student_id}` — get current streak
  - `POST /student/streak/{student_id}/update` — record activity
- **`app/api/sync.py`** — Auto-updates streak on every sync

#### Frontend Changes
- **`src/pages/Home.jsx`** — Streak bar with:
  - Flame icon (pulses orange when streak > 0, grey when 0)
  - Current streak count and best streak
  - "Download Offline" button integrated into streak bar

---

### ⚡ 6. Daily Challenge

**Problem:** No special daily engagement feature.

#### Backend Changes
- **`app/api/student.py`** — Endpoints:
  - `GET /student/daily-challenge?grade=5&student_id=...` — get today's challenge (auto-creates from hard questions)
  - `POST /student/daily-challenge/complete` — mark completed, +50 bonus XP
- Daily challenge auto-selects a hard question per grade per day

#### Frontend Changes
- **`src/pages/Home.jsx`** — Teal gradient card with:
  - Lightning bolt icon
  - "+50 XP" bonus badge
  - "Start Challenge" button → navigates to quest
  - "Completed today!" state after finishing

---

### ⏱️ 7. Question Timer

**Problem:** No time pressure or urgency in quest answering.

#### Frontend Changes
- **`src/pages/Quest.jsx`** — Countdown timer:
  - Easy: 60 seconds, Medium: 90 seconds, Hard: 120 seconds
  - Timer pill in question header (green → amber → red)
  - Thin progress bar under pill row
  - Pulsing animation when under 15 seconds
  - Timer stops when answer submitted

---

### 📴 8. Offline Download

**Problem:** Students couldn't pre-download questions for offline use.

#### Backend Changes
- **`app/api/student.py`** — `GET /questions/download?grade=5&subject=Math&limit=200`

#### Frontend Changes
- **`src/pages/Home.jsx`** — "Download Offline" button:
  - Downloads 200 questions per subject (600 total) into Dexie/IndexedDB
  - Shows progress percentage while downloading
  - Works for Math, Science, English

---

### 🧠 9. SM-2 Spaced Repetition

**Problem:** No mechanism to schedule question reviews for long-term retention.

#### Backend Changes
- **`app/core/spaced_repetition.py`** — Full SM-2 algorithm:
  - `sm2_next_review(ease_factor, interval, quality)` — computes next review date
  - `outcome_to_quality(correct, time_ms, hints)` — converts interaction to quality score 0-5
- **`app/api/student.py`** — Endpoints:
  - `GET /student/spaced-review/{student_id}?grade=5` — questions due for review
  - `POST /student/spaced-review/update` — update schedule after answering
- **`src/pages/Quest.jsx`** — Calls `/student/spaced-review/update` after every answer

---

### 🗺️ 10. Prerequisite Knowledge Graph

**Problem:** Recommendation system could suggest algebra before fractions were mastered.

#### Backend Changes
- **`app/api/recommend.py`** — Added `PREREQUISITE_GRAPH`:
  ```python
  PREREQUISITE_GRAPH = {
      "fractions": ["multiplication", "division"],
      "algebra": ["fractions", "arithmetic"],
      "geometry_area": ["multiplication", "units"],
      "percentages": ["fractions", "multiplication"],
      "decimals": ["place_value", "fractions"],
      "linear_equations": ["algebra"],
      "trigonometry": ["geometry_area", "algebra"],
      "statistics": ["fractions", "percentages"],
  }
  ```
- Questions with unmet prerequisites get a -0.3 score penalty in recommendations

---

### 🏆 11. Leaderboard

**Problem:** No competitive element between students.

#### Backend Changes
- **`app/core/leaderboard_service.py`** — New service:
  - `upsert_student_stats()` — writes/updates student XP/level/badges to `student_leaderboard` collection
  - `get_leaderboard(grade, school=None)` — queries sorted by XP descending
- **`app/api/student.py`** — Endpoints:
  - `GET /leaderboard?grade=5&school=MySchool` — filtered leaderboard (same school)
  - `GET /leaderboard?grade=5` — all schools, same grade
  - `POST /leaderboard/update` — push stats directly
- **`app/api/sync.py`** — Auto-updates leaderboard on every sync

#### Frontend Changes
- **`src/pages/Progress.jsx`** — Full leaderboard section:
  - **Scope toggle**: "My School" vs "All Schools" (same grade)
  - **Top 3 Podium**: Gold/silver/bronze cards with avatar initials
  - **Full ranked list**: rank icon/number, avatar, name, school (in all-schools view), level badge, XP, badges, accuracy
  - **"You" highlight**: current student row highlighted in teal
  - **My Rank**: shown in stats grid at top
  - **Real-time**: stats pushed to MongoDB on page load
  - **Edge case**: shows single student if only one exists

#### Data Flow
```
Student answers quest → sync to backend → sync.py auto-updates leaderboard
→ MongoDB student_leaderboard collection → /leaderboard API → Progress page
```

---

### 📊 12. Teacher Dashboard Improvements

**Problem:** Teacher dashboard lacked visual tools for identifying struggling students.

#### Frontend Changes — `src/pages/TeacherDashboard.jsx`

**Skill Performance Heatmap:**
- Grid of topic cells colored by accuracy: green (≥80%), yellow (≥60%), orange (≥40%), red (<40%)
- Hover tooltip shows topic name, accuracy %, attempt count
- Populated from XAI root causes data

**At-Risk Student Alerts:**
- Red-bordered panel with `AlertTriangle` icon
- Shows students with accuracy < 40% after 5+ attempts
- "Needs Support" badge on each at-risk student
- Count badge in header

**Subject Radar Chart:**
- Recharts `RadarChart` showing class accuracy per subject
- Side-by-side with heatmap in two-column layout
- Collapses to single column on mobile

---

### 🔧 13. MongoDB Questions Not Showing on Student Dashboard

**Problem:** Teacher-uploaded questions weren't appearing in student recommendations.

#### Root Cause & Fix
- **`app/api/recommend.py`** — Grade filter was passing a string instead of `int(grade)`, causing MongoDB to miss questions. Fixed with `int(grade)`. Increased fetch limit from `limit*10` to `200`. Added error logging.
- **`src/services/learning.js`** — `fetchQuestion()` Dexie cache lookup was crashing silently on cache misses, preventing API fallback. Wrapped in try/catch.

---

### ⚙️ 14. Math Generator Expanded

**File:** `app/generators/math_generator.py`

Expanded to cover all grades 1-12 with unlimited procedural questions:
- Grades 1-3: Addition, Subtraction, Multiplication
- Grades 4-6: + Division, Fractions, Percentages
- Grades 7-12: + Algebra, Geometry (area of shapes)

Zero cost, infinite variations, deterministic by seed.

---

### 🚀 15. Auto-Translation on Server Startup

**File:** `app/main.py`

Added `@app.on_event("startup")` background task:
- Runs on every server start
- Finds up to 50 untranslated questions
- Translates them in batches of 5 with 2-second delays
- Respects Groq API rate limits

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



