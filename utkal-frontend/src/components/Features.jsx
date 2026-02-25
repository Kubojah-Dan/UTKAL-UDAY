import React from "react";

const features = [
  {
    title: "Adaptive Quests + XP",
    desc: "Students solve personalized questions, earn XP per problem, level up, and unlock badges for consistency and accuracy."
  },
  {
    title: "School + Grade Analytics",
    desc: "Teachers view insights filtered by school and class, including trends, subject mastery, and top student progress."
  },
  {
    title: "Offline and Sync",
    desc: "Attempts are saved locally and synced when internet is available, so learning continues in low-connectivity areas."
  },
  {
    title: "Math + Science + English",
    desc: "Preloaded grade-wise question bank now includes English alongside Mathematics and Science for wider classroom use."
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
