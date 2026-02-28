import React from "react";
import Hero from "../components/Hero";
import { FeaturesSection } from "../components/FeaturesSection";
import { CTASection } from "../components/CTASection";
import { Footer } from "../components/Footer";

const OFFERINGS = [
  {
    title: "Personalized Learning Paths",
    desc: "Recommendations adapt to each learner's performance so practice time is focused on weak skills."
  },
  {
    title: "Teacher Monitoring by School/Class",
    desc: "Dashboards support grade and school filtering so teachers can track the exact students they teach."
  },
  {
    title: "Gamified Motivation",
    desc: "Students earn XP, climb levels, and unlock badges as they solve more questions correctly."
  },
  {
    title: "Offline-First Delivery",
    desc: "The app keeps working in low-connectivity areas and syncs progress when internet is restored."
  }
];

const IMPACT_STATS = [
  {
    value: "98.1%",
    title: "Rural children (age 6-14) enrolled",
    desc: "Still leaves about 1.9% out of school in this age band.",
    source: "ASER 2024 (rural survey)"
  },
  {
    value: "7.9%",
    title: "Rural teens (age 15-16) not enrolled",
    desc: "Drop-off rises in higher age groups, indicating retention challenges.",
    source: "ASER 2024 (rural survey)"
  },
  {
    value: "73.5%",
    title: "Rural population (age 5+) can use internet",
    desc: "Roughly 1 in 4 still lacks practical internet use capability.",
    source: "MOSPI NSO survey (Jan-Mar 2025)"
  },
  {
    value: "83.3%",
    title: "Rural households with internet at home",
    desc: "Coverage improved, but usage and learning quality gaps remain.",
    source: "MOSPI NSO survey (Jan-Mar 2025)"
  }
];

const BENEFITS = [
  "Improves foundational skills with frequent short practice loops.",
  "Gives teachers actionable mastery and engagement data every week.",
  "Supports blended learning where internet is intermittent.",
  "Creates student motivation through points, levels, and badges."
];

export default function Landing() {
  return (
    <div className="landing-page flex flex-col min-h-screen">
      <main className="flex-1">
        <div className="container py-6">
          <Hero />
        </div>
        <FeaturesSection />

        <div className="container py-16">
          <section className="panel mb-12">
            <h2 className="section-title">What Utkal Quest Offers</h2>
            <div className="offer-grid">
              {OFFERINGS.map((item) => (
                <article key={item.title} className="offer-card">
                  <h3>{item.title}</h3>
                  <p>{item.desc}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="panel mb-12">
            <h2 className="section-title">Rural Education Access Snapshot (India)</h2>
            <p className="muted">
              These indicators help explain why offline-first and teacher-guided digital learning still matters.
            </p>
            <div className="impact-grid mt-6">
              {IMPACT_STATS.map((stat) => (
                <article key={stat.title} className="impact-card">
                  <strong className="text-2xl text-primary">{stat.value}</strong>
                  <h3 className="mt-2 text-lg font-semibold">{stat.title}</h3>
                  <p className="text-sm mt-1 mb-2">{stat.desc}</p>
                  <small className="text-xs text-muted-foreground">{stat.source}</small>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <h2 className="section-title">Benefits for Schools</h2>
            <div className="benefit-list mt-6 grid gap-4 md:grid-cols-2">
              {BENEFITS.map((item) => (
                <div key={item} className="benefit-item flex items-start gap-3 bg-muted/50 p-4 rounded-lg">
                  <div className="mt-1 flex-shrink-0 w-2 h-2 rounded-full bg-primary" />
                  <p className="text-sm">{item}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
