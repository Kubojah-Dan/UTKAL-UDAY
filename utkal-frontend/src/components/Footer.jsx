import React from "react";
import { Link } from "react-router-dom";
import { Github, Twitter, Linkedin, Mail } from "lucide-react";

export function Footer() {
    return (
        <footer className="bg-muted py-12 border-t border-border">
            <div className="container grid gap-8 md:grid-cols-4">
                <div className="space-y-4">
                    <h3 className="text-xl font-bold text-foreground">Utkal Quest</h3>
                    <p className="text-sm text-muted-foreground w-3/4">
                        AI-Driven Gamified Mastery for rural students. Offline-first, adaptive, and culturally grounded.
                    </p>
                    <div className="flex space-x-4">
                        <a href="https://x.com/kubojah014" className="text-muted-foreground hover:text-primary transition-colors">
                            <Twitter className="h-5 w-5" />
                        </a>
                        <a href="https://github.com/Kubojah-Dan/UTKAL-UDAY.git" className="text-muted-foreground hover:text-primary transition-colors">
                            <Github className="h-5 w-5" />
                        </a>
                        <a href="https://www.linkedin.com/in/kuboja-mabuba-9202b82b6" className="text-muted-foreground hover:text-primary transition-colors">
                            <Linkedin className="h-5 w-5" />
                        </a>
                    </div>
                </div>

                <div>
                    <h4 className="font-semibold text-foreground mb-4">Product</h4>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                        <li><Link to="/" className="hover:text-primary transition-colors">Features</Link></li>
                        <li><Link to="/" className="hover:text-primary transition-colors">Schools & Districts</Link></li>
                        <li><Link to="/" className="hover:text-primary transition-colors">Download App</Link></li>
                        <li><Link to="/" className="hover:text-primary transition-colors">Offline Sync Guide</Link></li>
                    </ul>
                </div>

                <div>
                    <h4 className="font-semibold text-foreground mb-4">Resources</h4>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                        <li><Link to="/" className="hover:text-primary transition-colors">About Us</Link></li>
                        <li><Link to="/" className="hover:text-primary transition-colors">Blog & Case Studies</Link></li>
                        <li><Link to="/" className="hover:text-primary transition-colors">Help Center</Link></li>
                        <li><Link to="/" className="hover:text-primary transition-colors">Pedagogy Research</Link></li>
                    </ul>
                </div>

                <div>
                    <h4 className="font-semibold text-foreground mb-4">Contact</h4>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                        <li className="flex items-center gap-2">
                            <Mail className="h-4 w-4" />
                            <a href="mailto:hello@utkalquest.in" className="hover:text-primary transition-colors">hello@utkalquest.in</a>
                        </li>
                        <li>Coimbatore, Tamil Nadu, India</li>
                    </ul>
                </div>
            </div>

            <div className="container mt-12 pt-8 border-t border-border/50 text-sm py-4 flex flex-col md:flex-row justify-between items-center text-muted-foreground">
                <p>© {new Date().getFullYear()} Utkal Quest. All rights reserved.</p>
                <div className="flex space-x-4 mt-4 md:mt-0">
                    <Link to="/" className="hover:text-primary transition-colors">Privacy Policy</Link>
                    <Link to="/" className="hover:text-primary transition-colors">Terms of Service</Link>
                </div>
            </div>
        </footer>
    );
}
