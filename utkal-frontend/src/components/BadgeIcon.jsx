import React from "react";
import {
  Medal,
  Target,
  Shield,
  Zap,
  Compass,
  Crown,
  Star,
  BookOpen,
  FlaskConical,
  Rocket,
  Globe2
} from "lucide-react";

const ICONS = {
  medal: Medal,
  target: Target,
  shield: Shield,
  bolt: Zap,
  compass: Compass,
  crown: Crown,
  star: Star,
  book: BookOpen,
  flask: FlaskConical,
  rocket: Rocket,
  globe: Globe2
};

export default function BadgeIcon({ icon = "medal", className = "w-6 h-6" }) {
  const Icon = ICONS[icon] || Medal;
  return (
    <span className={`badge-icon inline-flex items-center justify-center ${className}`} aria-hidden="true">
      <Icon className="w-full h-full" />
    </span>
  );
}
