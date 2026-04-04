import React, { useEffect } from "react";
import { Link, Navigate } from "react-router-dom";
import { ArrowRight, ExternalLink } from "lucide-react";
import { Footer } from "../components/Footer";
import { sitePages } from "../content/sitePages";

function ActionButton({ action, primary = false }) {
  if (!action) return null;

  const className = primary ? "btn-primary" : "btn-outline";
  const content = (
    <>
      <span>{action.label}</span>
      {action.href ? <ExternalLink className="w-4 h-4" /> : <ArrowRight className="w-4 h-4" />}
    </>
  );

  if (action.href) {
    const isExternal = /^(https?:|mailto:)/i.test(action.href);
    return (
      <a
        href={action.href}
        className={className}
        target={isExternal ? "_blank" : undefined}
        rel={isExternal ? "noopener noreferrer" : undefined}
      >
        {content}
      </a>
    );
  }

  return (
    <Link to={action.to || "/"} className={className}>
      {content}
    </Link>
  );
}

export default function InfoPage({ pageKey }) {
  const page = sitePages[pageKey];

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [pageKey]);

  if (!page) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <div className="container flex-1 py-10">
        <section className="panel overflow-hidden">
          <div className="rounded-[2rem] border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-teal-100 p-8 md:p-10">
            <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-900">
              {page.eyebrow}
            </span>
            <h1 className="mt-4 max-w-3xl text-3xl font-black tracking-tight text-slate-900 md:text-5xl">
              {page.title}
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-700 md:text-lg">
              {page.summary}
            </p>

            {page.highlights?.length ? (
              <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {page.highlights.map((item) => (
                  <span
                    key={item}
                    className="rounded-2xl border border-emerald-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm"
                  >
                    {item}
                  </span>
                ))}
              </div>
            ) : null}

            <div className="mt-8 flex flex-wrap gap-3">
              <ActionButton action={page.primaryAction} primary />
              <ActionButton action={page.secondaryAction} />
            </div>
          </div>
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          {(page.sections || []).map((section, index) => (
            <section key={section.title} className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-800">
                  <span className="text-lg font-bold">{index + 1}</span>
                </div>
                <h2 className="text-xl font-semibold text-slate-900">{section.title}</h2>
              </div>
              <p className="mt-4 text-sm leading-7 text-slate-600">{section.body}</p>
              {section.bullets?.length ? (
                <ul className="mt-5 space-y-3 text-sm text-slate-700">
                  {section.bullets.map((bullet) => (
                    <li key={bullet} className="flex gap-3 rounded-2xl border border-amber-100 bg-amber-50/70 p-4">
                      <span className="mt-1 h-2.5 w-2.5 rounded-full bg-amber-500" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </section>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
