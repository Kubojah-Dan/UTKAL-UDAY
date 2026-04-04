export const sitePages = {
  features: {
    eyebrow: "Product",
    title: "Features",
    summary:
      "Utkal Uday combines adaptive quests, offline-first delivery, multilingual support, and teacher analytics in one classroom-friendly learning platform.",
    highlights: ["Offline sync", "Adaptive quests", "Teacher dashboards", "Quiz notifications"],
    sections: [
      {
        title: "Student Learning Loop",
        body:
          "Students move through short quests, quizzes, and streak-based practice. The platform adapts difficulty and recommends the next skill based on recent performance.",
        bullets: ["XP, badges, and levels keep motivation high.", "Questions work across web and the Android app.", "Language variants can be delivered as they become available."],
      },
      {
        title: "Teacher Visibility",
        body:
          "Teachers can upload content, create timed quizzes, review analytics by grade and school, and identify who needs support before gaps widen.",
        bullets: ["Risk-focused analytics highlight struggling students.", "Quiz analytics now surface both attempts and absentees.", "Announcements can be targeted to the exact class."],
      },
      {
        title: "Built for Low-Connectivity Contexts",
        body:
          "The app caches core learning content locally, supports background sync, and keeps students working even when the network is unreliable.",
      },
    ],
    primaryAction: { label: "Download App", to: "/download-app" },
    secondaryAction: { label: "Open Web App", to: "/login" },
  },
  "schools-districts": {
    eyebrow: "Partnerships",
    title: "Schools & Districts",
    summary:
      "The platform is designed for grade-level rollout, teacher oversight, and school-specific use across multiple classrooms.",
    highlights: ["School-scoped data", "Grade targeting", "Teacher dashboards", "Offline readiness"],
    sections: [
      {
        title: "What Schools Get",
        body:
          "Each teacher sees the students in the same school context and can monitor mastery, participation, and quiz response patterns without leaving the app.",
        bullets: ["Class-grade filtering for classroom-level review.", "Attendance visibility for time-bound quizzes.", "Teacher-created question banks for local curriculum alignment."],
      },
      {
        title: "District Rollout Readiness",
        body:
          "Because the frontend can be shipped as both web and Android, schools can start with browser access and add APK distribution as devices become available.",
      },
      {
        title: "Implementation Pattern",
        body:
          "Start with one school and one grade, review engagement and content quality, then expand class-by-class with quiz notifications and offline download packs enabled.",
      },
    ],
    primaryAction: { label: "Contact Us", to: "/contact" },
    secondaryAction: { label: "Read Pedagogy Research", to: "/pedagogy-research" },
  },
  "offline-sync-guide": {
    eyebrow: "Operations",
    title: "Offline Sync Guide",
    summary:
      "Students can keep solving questions offline. Interactions are saved locally and sent once the device reconnects.",
    highlights: ["Local storage", "Auto sync", "Retry queue", "Low-bandwidth ready"],
    sections: [
      {
        title: "How It Works",
        body:
          "Question data is cached on the device, learning events are stored locally, and the app retries synchronization whenever the device comes back online.",
        bullets: ["Offline question packs can be downloaded by subject.", "Sync also runs when the app becomes visible again.", "Students do not lose answers when the network drops mid-session."],
      },
      {
        title: "Best Classroom Practice",
        body:
          "Ask students to open the app while connected at least once a day so new quizzes, translations, and teacher notices can refresh in the background.",
      },
      {
        title: "Teacher Tip",
        body:
          "When announcing a timed quiz, remind students to connect before the 24-hour window closes so they receive the latest notification and quiz content.",
      },
    ],
    primaryAction: { label: "Download App", to: "/download-app" },
    secondaryAction: { label: "Help Center", to: "/help-center" },
  },
  about: {
    eyebrow: "Company",
    title: "About Us",
    summary:
      "Utkal Uday is built to make adaptive digital learning usable in real classrooms, especially where devices, bandwidth, and teacher time are limited.",
    highlights: ["Rural-first", "Teacher-led", "Offline-first", "Classroom practical"],
    sections: [
      {
        title: "Why We Built It",
        body:
          "Students need more than a question bank. They need guided practice, feedback, motivation, and teachers need tools that are fast enough to use during school hours.",
      },
      {
        title: "What We Value",
        body:
          "We focus on real classroom use: easy login, local content, multilingual support, teacher workflow help, and mobile access for students who use phones.",
      },
      {
        title: "Where We Are Based",
        body:
          "The project references Coimbatore, Tamil Nadu, India in the current product profile, while supporting use cases that extend into broader Indian classroom contexts.",
      },
    ],
    primaryAction: { label: "Get in Touch", to: "/contact" },
    secondaryAction: { label: "Privacy Policy", to: "/privacy-policy" },
  },
  "blog-case-studies": {
    eyebrow: "Resources",
    title: "Blog & Case Studies",
    summary:
      "This section highlights rollout stories, classroom observations, and product notes that help schools understand how the platform is being used.",
    highlights: ["Pilot stories", "Teacher insights", "Rollout notes", "Product updates"],
    sections: [
      {
        title: "Case Study Format",
        body:
          "Document pilot grade, school context, internet constraints, student completion rates, and the teacher interventions that had the biggest effect.",
      },
      {
        title: "Suggested Topics",
        body:
          "Useful future posts include offline rollout lessons, quiz engagement improvement, multilingual adoption, and teacher workflow simplification.",
      },
      {
        title: "Publishing Direction",
        body:
          "You can expand this page later into a CMS or markdown-backed blog without changing the footer routing structure.",
      },
    ],
    primaryAction: { label: "Contact Us", to: "/contact" },
    secondaryAction: { label: "Help Center", to: "/help-center" },
  },
  "help-center": {
    eyebrow: "Support",
    title: "Help Center",
    summary:
      "Find quick answers for students, teachers, and school staff using the web app, offline mode, quizzes, and mobile access.",
    highlights: ["Login help", "Quiz help", "Offline help", "Teacher support"],
    sections: [
      {
        title: "Student FAQs",
        body:
          "Students can change their language, download content for offline use, complete daily challenges, and pick up where they left off in a quiz.",
      },
      {
        title: "Teacher FAQs",
        body:
          "Teachers can create quizzes, share announcements, review participation, and see which students need extra support in the same class and grade.",
      },
      {
        title: "App connection help",
        body:
          "If the app cannot connect, make sure your device has an active internet connection and try again. If problems continue, contact your school support team for help.",
      },
    ],
    primaryAction: { label: "Download App", to: "/download-app" },
    secondaryAction: { label: "Contact Support", to: "/contact" },
  },
  "pedagogy-research": {
    eyebrow: "Research",
    title: "Pedagogy Research",
    summary:
      "The platform is structured around short feedback loops, teacher visibility, adaptive sequencing, and motivation through visible progress.",
    highlights: ["Mastery tracking", "Short practice loops", "Teacher intervention", "Motivation systems"],
    sections: [
      {
        title: "Learning Design",
        body:
          "Students receive frequent, low-friction practice opportunities. Performance data is converted into next-step recommendations rather than static content lists.",
      },
      {
        title: "Teacher Intervention Model",
        body:
          "Analytics aim to answer three practical questions: who is at risk, which skill is blocking progress, and who missed the latest quiz window.",
      },
      {
        title: "Why Offline Matters",
        body:
          "Pedagogy breaks when access is inconsistent. Offline-first delivery protects continuity and reduces the chance that students are excluded by weak connectivity.",
      },
    ],
    primaryAction: { label: "Features", to: "/features" },
    secondaryAction: { label: "Schools & Districts", to: "/schools-districts" },
  },
  "privacy-policy": {
    eyebrow: "Privacy",
    title: "Your privacy",
    summary:
      "We only keep the information needed to make the app work for you: your account, progress, and quiz history so your learning continues smoothly.",
    highlights: ["What we collect", "Why it matters", "How it is used", "How to contact us"],
    sections: [
      {
        title: "What we collect",
        body:
          "We store only the details required for your learning experience: name, email, school, role, grade, quiz attempts, question answers, and locally cached progress.",
      },
      {
        title: "Why it matters",
        body:
          "This information helps keep your account working, lets you pick up where you left off, supports teacher feedback, and keeps the app useful even when connectivity is weak.",
      },
      {
        title: "How we protect it",
        body:
          "Your information is used only to make the app work for you. We keep it limited to your account, progress, and learning activity so the experience stays useful and safe.",
      },
    ],
    primaryAction: { label: "Terms of Service", to: "/terms-of-service" },
    secondaryAction: { label: "Contact", to: "/contact" },
  },
  "terms-of-service": {
    eyebrow: "Terms",
    title: "Terms for using Utkal Uday",
    summary:
      "These terms explain how students, teachers, and schools should use the app and what to expect from a safe rollout.",
    highlights: ["Use your account", "Teacher guidance", "Classroom use", "Secure rollout"],
    sections: [
      {
        title: "Use your account responsibly",
        body:
          "Students and teachers should use the app features meant for their role. Teacher-only tools should stay with teacher accounts, and student accounts should not share that access.",
      },
      {
        title: "Teacher guidance",
        body:
          "Teachers should review and assign questions carefully, support learners with feedback, and use the app as a classroom tool rather than a shared administrative account.",
      },
      {
        title: "Safe school use",
        body:
          "For school use, the app should be delivered through trusted, secure channels so students can learn reliably without unnecessary risk.",
      },
    ],
    primaryAction: { label: "Privacy Policy", to: "/privacy-policy" },
    secondaryAction: { label: "Download App", to: "/download-app" },
  },
  contact: {
    eyebrow: "Contact",
    title: "Contact Us",
    summary:
      "Reach the team for school onboarding, pilot rollout support, product questions, or feedback about classroom use.",
    highlights: ["School onboarding", "Pilot support", "Product feedback", "Technical help"],
    sections: [
      {
        title: "Email",
        body: "Primary contact: hello@utkalquest.in",
      },
      {
        title: "Location",
        body: "Coimbatore, Tamil Nadu, India",
      },
      {
        title: "Best Use of This Channel",
        body:
          "Use this page for school rollout support, classroom pilot help, content questions, Android app installation help, and product feedback.",
      },
    ],
    primaryAction: { label: "Send Email", href: "mailto:hello@utkalquest.in" },
    secondaryAction: { label: "Schools & Districts", to: "/schools-districts" },
  },
};
