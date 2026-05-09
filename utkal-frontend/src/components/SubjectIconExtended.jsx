import React from "react";
import { SubjectIcon as BaseIcon } from "./SubjectIcon";

// Extended subject icon mapping for new subjects
const SUBJECT_ICONS = {
  "Environmental Science": (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22V12" /><path d="M12 12C12 7 8 3 3 3c0 5 4 8 9 9" /><path d="M12 12c0-5 4-9 9-9-1 5-5 8-9 9" />
    </svg>
  ),
  "Social Science": (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><path d="M2 12h20" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  ),
  "EVS": (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22V12" /><path d="M12 12C12 7 8 3 3 3c0 5 4 8 9 9" /><path d="M12 12c0-5 4-9 9-9-1 5-5 8-9 9" />
    </svg>
  ),
};

export default function SubjectIcon({ subject, className }) {
  const svgIcon = SUBJECT_ICONS[subject];
  if (svgIcon) {
    return (
      <span className={`subject-icon ${className || ""}`}>
        {svgIcon}
      </span>
    );
  }
  // Fall back to the base component for existing subjects
  return <BaseIcon subject={subject} className={className} />;
}
