import React from "react";

const features = [
  {
    title: "Student Quest Flow",
    desc: "Students solve adaptive questions with hints, track mastery, and progress through interactive learning paths."
  },
  {
    title: "Teacher Analytics",
    desc: "Teachers monitor class activity, accuracy trends, and learning gaps with actionable visual summaries."
  },
  {
    title: "Offline and Sync",
    desc: "Attempts are saved locally and synced when internet is available, so learning continues in low-connectivity areas."
  },
  {
    title: "Math + Science Starter Bank",
    desc: "Preloaded grade-wise questions aligned with Indian curriculum themes to begin classroom pilots quickly."
  }
];

export default function Features() {
  return (
    <section className="feature-grid">
      {features.map((item) => (
        <article key={item.title} className="feature-card">
          <h3>{item.title}</h3>
          <p>{item.desc}</p>
        </article>
      ))}
    </section>
  );
}
