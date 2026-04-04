import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, Download, ExternalLink, Globe, ShieldCheck, Smartphone, Wifi } from "lucide-react";
import { Footer } from "../components/Footer";
import { useAuth } from "../context/AuthContext";

const apkUrl = (import.meta.env.VITE_ANDROID_APK_URL || "").trim();

function openWebRoute(user) {
  if (!user) return "/login";
  return user.role === "teacher" ? "/teacher" : "/home";
}

const highlights = [
  {
    icon: Smartphone,
    title: "Made for Android phones",
    body: "A simple install flow for students, teachers, and school coordinators using Android devices in the field.",
  },
  {
    icon: Wifi,
    title: "Built for low-connectivity use",
    body: "Core learning flows are designed for classrooms where internet is intermittent and mobile access matters.",
  },
  {
    icon: ShieldCheck,
    title: "Same trusted Utkal Uday experience",
    body: "Learners can sign in with the same account and continue with quests, quizzes, and progress tracking.",
  },
];

const installSteps = [
  "Tap the download button and save the APK to your device.",
  "Open the downloaded file and allow installation if Android asks for permission.",
  "Launch Utkal Uday and sign in with your student or teacher account.",
];

const afterInstall = [
  "Access quests, quizzes, and classroom updates from one app.",
  "Keep learning even when internet quality drops during the day.",
  "Return to the web version anytime using the same account.",
];

export default function DownloadApp() {
  const { user } = useAuth();
  const webRoute = openWebRoute(user);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <div className="container flex-1 py-10">
        <section className="panel overflow-hidden">
          <div className="rounded-[2rem] bg-gradient-to-br from-teal-950 via-teal-800 to-emerald-600 p-8 text-white md:p-12">
            <span className="inline-flex rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-teal-50">
              Android App
            </span>
            <h1 className="mt-5 max-w-3xl text-3xl font-black tracking-tight md:text-5xl">
              Download Utkal Uday and bring learning directly to your phone
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-teal-50/90 md:text-lg">
              Get quick access to quests, quizzes, and teacher updates in a mobile experience designed for everyday classroom use.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              {apkUrl ? (
                <a href={apkUrl} target="_blank" rel="noopener noreferrer" className="btn-primary">
                  <Download className="h-4 w-4" />
                  <span>Download APK</span>
                </a>
              ) : (
                <button className="btn-primary" disabled>
                  <Download className="h-4 w-4" />
                  <span>APK Coming Soon</span>
                </button>
              )}

              <Link to={webRoute} className="btn-outline border-white/30 bg-white/5 text-white hover:bg-white/10">
                <Globe className="h-4 w-4" />
                <span>Open Web Version</span>
              </Link>
            </div>

            <div className="mt-5 text-sm text-teal-50/80">
              {apkUrl
                ? "If the download does not start automatically, open the link in your phone browser and try again."
                : "The Android download link will appear here as soon as the release APK is published."}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-3">
          {highlights.map(({ icon: Icon, title, body }) => (
            <article key={title} className="panel">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-100 text-teal-800">
                <Icon className="h-5 w-5" />
              </div>
              <h2 className="mt-4 text-xl font-bold text-slate-900">{title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{body}</p>
            </article>
          ))}
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
          <article className="panel">
            <h2 className="text-2xl font-bold text-slate-900">How to install</h2>
            <div className="mt-5 space-y-4">
              {installSteps.map((step, index) => (
                <div key={step} className="flex items-start gap-4 rounded-2xl bg-slate-50 p-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-700 text-sm font-bold text-white">
                    {index + 1}
                  </div>
                  <p className="pt-1 text-sm leading-7 text-slate-700">{step}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <h2 className="text-2xl font-bold text-slate-900">After installation</h2>
            <ul className="mt-5 space-y-4">
              {afterInstall.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm leading-7 text-slate-700">
                  <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-teal-700" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8 rounded-2xl border border-teal-100 bg-teal-50 p-5">
              <p className="text-sm font-semibold text-slate-900">Need the latest release link for your school rollout?</p>
              <a
                href="mailto:hello@utkalquest.in"
                className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-teal-800"
              >
                <span>Contact the team</span>
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </article>
        </section>
      </div>
      <Footer />
    </div>
  );
}
