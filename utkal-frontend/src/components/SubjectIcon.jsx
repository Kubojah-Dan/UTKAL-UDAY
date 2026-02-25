import React from "react";

function MathsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="4" y="3" width="16" height="18" rx="3" fill="currentColor" opacity="0.18" />
      <rect x="7" y="6" width="10" height="3" rx="1" fill="currentColor" />
      <rect x="7" y="11" width="4" height="4" rx="1" fill="currentColor" />
      <rect x="13" y="11" width="4" height="4" rx="1" fill="currentColor" />
      <rect x="7" y="16" width="10" height="2" rx="1" fill="currentColor" />
    </svg>
  );
}

function ScienceIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 3h4v2l-1 2v3.2l4.9 8.5A1.5 1.5 0 0 1 16.6 21H7.4a1.5 1.5 0 0 1-1.3-2.3L11 10.2V7L10 5V3Z" fill="currentColor" opacity="0.2" />
      <path d="M10 3h4v2l-1 2v3.2l4.9 8.5A1.5 1.5 0 0 1 16.6 21H7.4a1.5 1.5 0 0 1-1.3-2.3L11 10.2V7L10 5V3Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="10" cy="16" r="1" fill="currentColor" />
      <circle cx="13" cy="15" r="1" fill="currentColor" />
      <circle cx="12" cy="18" r="1" fill="currentColor" />
    </svg>
  );
}

function EnglishIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H12v14H6.5A2.5 2.5 0 0 0 4 20.5V6.5Z" fill="currentColor" opacity="0.2" />
      <path d="M20 6.5A2.5 2.5 0 0 0 17.5 4H12v14h5.5A2.5 2.5 0 0 1 20 20.5V6.5Z" fill="currentColor" opacity="0.1" />
      <path d="M12 4v14M4 6.5A2.5 2.5 0 0 1 6.5 4H12v14H6.5A2.5 2.5 0 0 0 4 20.5V6.5ZM20 6.5A2.5 2.5 0 0 0 17.5 4H12v14h5.5A2.5 2.5 0 0 1 20 20.5V6.5Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 9h2M8 12h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M14 9h2M14 12h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

const subjectKey = (value) => String(value || "").trim().toLowerCase();

export default function SubjectIcon({ subject, className = "" }) {
  const key = subjectKey(subject);
  let Icon = MathsIcon;
  if (key.startsWith("sci")) Icon = ScienceIcon;
  if (key.startsWith("eng")) Icon = EnglishIcon;
  if (key.startsWith("mat")) Icon = MathsIcon;

  return (
    <span className={`subject-icon ${className}`.trim()} title={subject || "Subject"}>
      <Icon />
    </span>
  );
}
