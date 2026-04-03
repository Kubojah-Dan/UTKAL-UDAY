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
    <div className="flex min-h-screen flex-col">
      <div className="container flex-1 py-10">
        <section className="panel overflow-hidden">
          <div className="rounded-2xl border border-teal-100 bg-gradient-to-br from-teal-50 via-white to-cyan-50 p-8 md:p-10">
            <span className="inline-flex rounded-full bg-teal-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-teal-800">
              {page.eyebrow}
            </span>
            <h1 className="mt-4 text-3xl font-black tracking-tight text-slate-900 md:text-5xl">{page.title}</h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600 md:text-lg">{page.summary}</p>

            {page.highlights?.length ? (
              <div className="mt-6 flex flex-wrap gap-3">
                {page.highlights.map((item) => (
                  <span key={item} className="rounded-full border border-teal-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm">
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
          {(page.sections || []).map((section) => (
            <section key={section.title} className="panel h-full">
              <h2 className="text-xl font-bold text-slate-900">{section.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{section.body}</p>
              {section.bullets?.length ? (
                <ul className="mt-5 space-y-3 text-sm text-slate-700">
                  {section.bullets.map((bullet) => (
                    <li key={bullet} className="flex gap-3">
                      <span className="mt-2 h-2 w-2 rounded-full bg-teal-600" />
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
