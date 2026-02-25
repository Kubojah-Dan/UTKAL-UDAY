import React from "react";

function Medal() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="14" r="6" fill="currentColor" opacity="0.2" />
      <path d="M9 3h2l1 4h-2L9 3Zm4 0h2l-1 4h-2l1-4Z" fill="currentColor" />
      <circle cx="12" cy="14" r="4" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function Target() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="1.8" fill="currentColor" />
    </svg>
  );
}

function Shield() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3 5.5 6v5.5c0 4.3 2.6 7.9 6.5 9.5 3.9-1.6 6.5-5.2 6.5-9.5V6L12 3Z" fill="currentColor" opacity="0.2" />
      <path d="M12 3 5.5 6v5.5c0 4.3 2.6 7.9 6.5 9.5 3.9-1.6 6.5-5.2 6.5-9.5V6L12 3Z" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function Bolt() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M13 2 6 13h5l-1 9 8-12h-5l0-8Z" fill="currentColor" />
    </svg>
  );
}

function Compass() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="m9 15 2-6 4-1-1 4-5 3Z" fill="currentColor" />
    </svg>
  );
}

function Crown() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m4 8 4 4 4-6 4 6 4-4-2 10H6L4 8Z" fill="currentColor" opacity="0.2" />
      <path d="m4 8 4 4 4-6 4 6 4-4-2 10H6L4 8Zm2 10h12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Star() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m12 3 2.5 5.1 5.7.8-4.1 4 1 5.7L12 16l-5.1 2.6 1-5.7-4.1-4 5.7-.8L12 3Z" fill="currentColor" opacity="0.25" />
      <path d="m12 3 2.5 5.1 5.7.8-4.1 4 1 5.7L12 16l-5.1 2.6 1-5.7-4.1-4 5.7-.8L12 3Z" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

function Book() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v16H7.5A2.5 2.5 0 0 0 5 21V5.5Z" fill="currentColor" opacity="0.2" />
      <path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v16H7.5A2.5 2.5 0 0 0 5 21V5.5Zm0 0V21m4-13h7m-7 4h7" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Flask() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 3h4m-3 0v5l-5.8 9.5A2 2 0 0 0 6.9 21h10.2a2 2 0 0 0 1.7-3.5L13 8V3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8.8 15h6.4l2 3.2H6.8l2-3.2Z" fill="currentColor" opacity="0.25" />
    </svg>
  );
}

function Rocket() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M14.5 4c2.5.3 5.2 3 5.5 5.5L14 15l-5-5 5.5-6Z" fill="currentColor" opacity="0.2" />
      <path d="M14.5 4c2.5.3 5.2 3 5.5 5.5L14 15l-5-5 5.5-6Zm-5.4 6.3L5 11l-1 4 4-1 1.1-3.7Zm5.8 5.8L14 20l4-1-1-4-3.1 1.1Z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="14.5" cy="9.5" r="1.2" fill="currentColor" />
    </svg>
  );
}

function Globe() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 12h16M12 4a13 13 0 0 1 0 16m0-16a13 13 0 0 0 0 16" fill="none" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

const ICONS = {
  medal: Medal,
  target: Target,
  shield: Shield,
  bolt: Bolt,
  compass: Compass,
  crown: Crown,
  star: Star,
  book: Book,
  flask: Flask,
  rocket: Rocket,
  globe: Globe
};

export default function BadgeIcon({ icon = "medal" }) {
  const Icon = ICONS[icon] || Medal;
  return (
    <span className="badge-icon" aria-hidden="true">
      <Icon />
    </span>
  );
}
