# Utkal Uday

Utkal Uday is a comprehensive educational platform designed to empower students through procedural quest-based learning and provide teachers with advanced AI-driven analytics. The system integrates a modern React frontend with a robust FastAPI backend, featuring Knowledge Tracing (KT) and Explainable AI (XAI) for personalized education.

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

### Frontend (`utkal-frontend/.env`)
- `VITE_API_BASE`: Backend URL (e.g., `http://localhost:8000`)
- `VITE_ANDROID_API_BASE`: Backend URL for Android emulator (`http://10.0.2.2:8000`)

### Backend (`utkal-backend/.env`)
- `UTKAL_TEACHER_PASSWORD`: Default login for teachers.
- `UTKAL_AUTH_SECRET`: JWT secret key.
- `MONGODB_URL`: Connection string for MongoDB.

---

## 📜 License

[Specify License Here]
