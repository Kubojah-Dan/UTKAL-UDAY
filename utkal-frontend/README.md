## Utkal Frontend (React + JavaScript)

### What Is Implemented

- Student quest UI supports:
  - Standard questions
  - XES image questions (`question_images`)
  - Analysis images (`analysis_images`) when hints are used
  - Multi-answer checking via `accepted_answers`
- Teacher dashboard upgrades:
  - Interactive daily trend (attempts + accuracy)
  - XAI dependency graph visualization
  - Root-cause, prerequisite GPA-gap, and causal-chain panels
- Expanded badge/icon system:
  - More badge categories and icon variants

### Run

```bash
npm install
npm run dev
```

### Build (PWA/Web)

```bash
npm run build
npm run preview
```

### Android/Play Store Wrapper (Capacitor)

```bash
npm run build
npx cap add android
npx cap sync
npx cap open android
```

### Login Roles

- `Student`: name required, student id optional.
- `Teacher`: default password is `teacher123` (change via backend env `UTKAL_TEACHER_PASSWORD`).

### API Base

Set in `.env`:

- `VITE_API_BASE=http://127.0.0.1:8000`
- `VITE_ANDROID_API_BASE=http://10.0.2.2:8000`
- `VITE_ANDROID_APK_URL=https://your-public-apk-url` (optional, used by the Download App page)

When running inside a Capacitor Android shell, the app now prefers `VITE_ANDROID_API_BASE`.
For a physical phone, point `VITE_ANDROID_API_BASE` to your deployed backend URL or your computer's LAN IP, not `127.0.0.1`.
