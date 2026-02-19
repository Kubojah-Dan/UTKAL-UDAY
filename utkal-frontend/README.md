## Utkal Frontend (React + JavaScript)

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
