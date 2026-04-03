import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download, ExternalLink, LaptopMinimal, Smartphone, Wifi } from "lucide-react";
import { Footer } from "../components/Footer";
import { useAuth } from "../context/AuthContext";

const apkUrl = (import.meta.env.VITE_ANDROID_APK_URL || "").trim();

export default function DownloadApp() {
  const [installEvent, setInstallEvent] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    const handler = (event) => {
      event.preventDefault();
      setInstallEvent(event);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const installPwa = async () => {
    if (!installEvent) return;
    installEvent.prompt();
    await installEvent.userChoice;
    setInstallEvent(null);
  };

  const webRoute = !user ? "/login" : user.role === "teacher" ? "/teacher" : "/home";

  return (
    <div className="flex min-h-screen flex-col">
      <div className="container flex-1 py-10">
        <section className="panel overflow-hidden">
          <div className="rounded-2xl border border-sky-100 bg-gradient-to-br from-sky-50 via-white to-teal-50 p-8 md:p-10">
            <span className="inline-flex rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-800">
              Mobile Access
            </span>
            <h1 className="mt-4 text-3xl font-black tracking-tight text-slate-900 md:text-5xl">Download App</h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600 md:text-lg">
              Use the web version immediately, install the PWA from your browser, or publish a signed Android APK from Android Studio once your release build is ready.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              {apkUrl ? (
                <a href={apkUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">
                  <Download className="w-4 h-4" />
                  <span>Download Android APK</span>
                </a>
              ) : (
                <button className="btn-primary" disabled>
                  <Download className="w-4 h-4" />
                  <span>APK Link Not Published Yet</span>
                </button>
              )}

              {installEvent ? (
                <button className="btn-outline" onClick={installPwa}>
                  <Smartphone className="w-4 h-4" />
                  <span>Install Web App</span>
                </button>
              ) : null}

              <Link to={webRoute} className="btn-outline">
                <LaptopMinimal className="w-4 h-4" />
                <span>Open Web Version</span>
              </Link>
            </div>
          </div>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <section className="panel">
            <h2 className="text-xl font-bold text-slate-900">1. Build the Web App</h2>
            <div className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
              <p>Inside `utkal-frontend`, set your production API values, then run:</p>
              <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-slate-100">{`npm install\nnpm run build`}</pre>
            </div>
          </section>

          <section className="panel">
            <h2 className="text-xl font-bold text-slate-900">2. Sync Capacitor Android</h2>
            <div className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
              <p>With Android Studio installed, run:</p>
              <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-slate-100">{`npx cap add android\nnpx cap sync android\nnpx cap open android`}</pre>
              <p>For emulator testing, `VITE_ANDROID_API_BASE` can stay on `http://10.0.2.2:8000`.</p>
            </div>
          </section>

          <section className="panel">
            <h2 className="text-xl font-bold text-slate-900">3. Generate the APK</h2>
            <div className="mt-4 space-y-3 text-sm leading-7 text-slate-600">
              <p>In Android Studio, let Gradle sync finish, then use `Build &gt; Generate Signed Bundle / APK`.</p>
              <p>Point `VITE_ANDROID_API_BASE` to your deployed backend URL or your computer&apos;s LAN IP for a real phone.</p>
              <a
                href="https://developer.android.com/studio/publish/app-signing"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-semibold text-teal-700"
              >
                <span>Android signing guide</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </section>
        </div>

        <section className="panel mt-8">
          <div className="flex items-start gap-3">
            <Wifi className="mt-1 h-5 w-5 text-teal-700" />
            <div>
              <h2 className="text-xl font-bold text-slate-900">Release Checklist</h2>
              <ul className="mt-4 space-y-3 text-sm text-slate-700">
                <li>Set `VITE_API_BASE` and `VITE_ANDROID_API_BASE` to a reachable backend URL.</li>
                <li>Deploy the backend first and confirm `/health` works publicly.</li>
                <li>Rotate local development secrets before publishing the app.</li>
                <li>Once the APK URL is ready, set `VITE_ANDROID_APK_URL` so this page can download it directly.</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
      <Footer />
    </div>
  );
}
