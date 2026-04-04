import React from "react";
import { Link } from "react-router-dom";
import { Github, Linkedin, Mail, MapPin, Twitter } from "lucide-react";

const productLinks = [
  { label: "Features", to: "/features" },
  { label: "Schools & Districts", to: "/schools-districts" },
  { label: "Download App", to: "/download-app" },
  { label: "Offline Sync Guide", to: "/offline-sync-guide" },
];

const resourceLinks = [
  { label: "About Us", to: "/about" },
  { label: "Blog & Case Studies", to: "/blog-case-studies" },
  { label: "Help Center", to: "/help-center" },
  { label: "Pedagogy Research", to: "/pedagogy-research" },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-muted py-12">
      <div className="container grid gap-8 md:grid-cols-4">
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-foreground">Utkal Quest</h3>
          <p className="w-3/4 text-sm text-muted-foreground">
            AI-driven, offline-first learning for students and teachers who need a platform that still works when connectivity does not.
          </p>
          <div className="flex space-x-4">
            <a
              href="https://x.com/kubojah014"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground transition-colors hover:text-primary"
              aria-label="Utkal Quest on X"
            >
              <Twitter className="h-5 w-5" />
            </a>
            <a
              href="https://github.com/Kubojah-Dan/UTKAL-UDAY.git"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground transition-colors hover:text-primary"
              aria-label="Utkal Quest on GitHub"
            >
              <Github className="h-5 w-5" />
            </a>
            <a
              href="https://www.linkedin.com/in/kuboja-mabuba-9202b82b6"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground transition-colors hover:text-primary"
              aria-label="Utkal Quest on LinkedIn"
            >
              <Linkedin className="h-5 w-5" />
            </a>
          </div>
        </div>

        <div>
          <h4 className="mb-4 font-semibold text-foreground">Product</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {productLinks.map((item) => (
              <li key={item.label}>
                <Link to={item.to} className="transition-colors hover:text-primary">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="mb-4 font-semibold text-foreground">Resources</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {resourceLinks.map((item) => (
              <li key={item.label}>
                <Link to={item.to} className="transition-colors hover:text-primary">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="mb-4 font-semibold text-foreground">
            <Link to="/contact" className="transition-colors hover:text-primary">
              Contact
            </Link>
          </h4>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              <a href="mailto:hello@utkalquest.in" className="transition-colors hover:text-primary">
                hello@utkalquest.in
              </a>
            </li>
            <li className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              <Link to="/contact" className="transition-colors hover:text-primary">
                Coimbatore, Tamil Nadu, India
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="container mt-12 flex flex-col items-center justify-between gap-4 border-t border-border/50 py-4 text-sm text-muted-foreground md:flex-row">
        <p>© {new Date().getFullYear()} Utkal Quest. All rights reserved.</p>
        <div className="flex space-x-4">
          <Link to="/privacy-policy" className="transition-colors hover:text-primary">
            Privacy
          </Link>
          <Link to="/terms-of-service" className="transition-colors hover:text-primary">
            Terms
          </Link>
        </div>
      </div>
    </footer>
  );
}
