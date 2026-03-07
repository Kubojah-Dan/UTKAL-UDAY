# Utkal Uday

Utkal Uday is a comprehensive educational platform designed to empower students through procedural quest-based learning and provide teachers with advanced AI-driven analytics. The system integrates a modern React frontend with a robust FastAPI backend, featuring Knowledge Tracing (KT) and Explainable AI (XAI) for personalized education.

**🎯 Built for rural Indian students (Grades 1-12) with multi-language support including Tamil.**

---

## 🚀 Quick Start

**New to the project? Start here:**

1. **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
2. **[FEATURES_SUMMARY.md](FEATURES_SUMMARY.md)** - See what's implemented
3. **[COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)** - Full feature overview

**Run setup script:**
```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

---

## ✨ New Features (All Implemented)

### 🌐 Multi-Language Support
- **10 Indian languages** including Tamil (தமிழ்), Hindi (हिंदी), Telugu, Kannada, Malayalam
- Powered by **Sarvam.ai** translation API
- Language selector in header
- Questions display in student's preferred language

### 📄 AI-Powered Document Processing
- Upload PDF or Word documents
- AI extracts and parses questions automatically
- Supports MCQ, descriptive, and image questions
- Batch approval and translation

### 🎯 Quiz System
- Structured assessments with timer
- Question navigation and review
- Instant results with detailed feedback
- XP calculation and progress tracking

### 🔄 Smart Question Rotation
- Students never see repeated questions
- Tracks attempted questions per student
- Automatic fallback when all questions attempted
- MongoDB-based tracking

### 📊 Enhanced Teacher Analytics
- **Causal Chains** - Skill dependency paths (now populated)
- **Prerequisite GPA Gaps** - Identify learning gaps (now populated)
- Root cause analysis
- Dynamic visualizations

### 🖼️ Image & Descriptive Questions
- Support for image-based MCQs
- 5-mark descriptive questions
- Expected points for grading
- AI-suggested image queries

### 💾 Database Integration
- AI-generated questions saved to MongoDB
- Approval workflow for teachers
- Content versioning
- Question bank management

---

## 🚀 Project Overview

The project consists of two main components:
1.  **utkal-frontend**: A React + Vite PWA/Mobile application for students and teachers.
2.  **utkal-backend**: A FastAPI server that handles data ingestion, AI model training, and student performance tracking.

---

## ✨ Key Features

### 🎓 Student Experience
- **Interactive Quests**: Support for standard, image-based (XES), and analysis questions.
- **AI-Driven Recommendations**: Personalized quest paths based on BKT mastery and DKT readiness signals.
- **Offline Capability**: PWA support with localized synchronization.
- **Achievement System**: Dynamic badge and icon rewards for student milestones.

### 👩‍🏫 Teacher Dashboard
- **XAI Analytics**: In-depth visualizations including dependency graphs and causal chains.
- **Performance Tracking**: Daily trends, accuracy metrics, and student-specific insights.
- **Root-Cause Analysis**: Identifying GPA gaps and prerequisite mastery issues.
- **AI-Powered Generation**: Procedural question generation for Grades 1-12 in Math, English, and Science.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS & DaisyUI
- **State/Data**: Axios, Dexie (IndexedDB), PouchDB
- **Animations**: Framer Motion
- **Visualization**: Recharts, Lucide Icons
- **Mobile**: Capacitor (Android support)

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB (via Motor/PyMongo)
- **AI/ML**: PyTorch (DKT), Scikit-learn, NumPy, Pandas
- **Graph Logic**: NetworkX, Pgmpy
- **Server**: Uvicorn

---

## ⚙️ Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.9+)
- MongoDB instance

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd utkal-uday
   ```

2. **Backend Setup**:
   ```bash
   cd utkal-backend
   pip install -r requirements.txt
   # Configure .env file
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**:
   ```bash
   cd utkal-frontend
   npm install
   # Configure .env file
   npm run dev
   ```

---

## 📱 Mobile Support (Android)

The frontend can be built as an Android app using Capacitor:
```bash
cd utkal-frontend
npm run build
npx cap sync
npx cap open android
```

---

## 🧬 AI & Models

The backend includes scripts for training Knowledge Tracing models:
```bash
# Train DKT and BKT models
py -m app.scripts.train_xes_models --epochs 10 --batch-size 128
```
Artifacts are stored in `utkal-backend/app/models/`.

---

## 🔑 Environment Configuration

### Backend (`utkal-backend/.env`)
```env
GROQ_API_KEY=your_groq_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here
MONGODB_URL=mongodb://localhost:27017/utkal_uday
UTKAL_TEACHER_PASSWORD=teacher123
UTKAL_AUTH_SECRET=your_jwt_secret_here
```

**Get API Keys:**
- **Groq API**: https://console.groq.com/keys (Free tier available)
- **Sarvam.ai API**: https://www.sarvam.ai/ (Contact for access)

### Frontend (`utkal-frontend/.env`)
```env
VITE_API_BASE=http://127.0.0.1:8000
VITE_ANDROID_API_BASE=http://10.0.2.2:8000
```

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[FEATURES_SUMMARY.md](FEATURES_SUMMARY.md)** - Quick feature reference
- **[COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md)** - Comprehensive overview
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Detailed technical guide
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Production deployment

---

## 📜 License

[Specify License Here]
