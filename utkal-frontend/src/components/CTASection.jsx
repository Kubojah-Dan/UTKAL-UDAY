import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Smartphone, ArrowRight } from "lucide-react";

export function CTASection() {
    const navigate = useNavigate();
    const { user } = useAuth();

    const handleDownloadAndroid = () => {
        navigate("/download-app");
    };

    const handleOpenWeb = () => {
        if (!user) {
            navigate("/login");
        } else if (user.role === "teacher") {
            navigate("/teacher");
        } else {
            navigate("/home");
        }
    };

    return (
        <section className="py-16 md:py-24 bg-gradient-to-br from-teal-600 to-teal-800 text-white">
            <div className="container text-center">
                <h2 className="text-3xl md:text-4xl font-bold mb-6">
                    Ready to Start Your Learning Quest?
                </h2>
                <p className="text-lg opacity-90 max-w-2xl mx-auto mb-8">
                    Join thousands of students in rural Odisha building mathematical intuition through gamified learning.
                </p>

                <div className="flex flex-wrap justify-center gap-4">
                    <button
                        onClick={handleDownloadAndroid}
                        className="btn-cta btn-cta-white"
                    >
                        <Smartphone className="h-5 w-5 mr-2" />
                        Download App
                    </button>
                    <button
                        onClick={handleOpenWeb}
                        className="btn-cta btn-cta-outline"
                    >
                        Open Web Version
                        <ArrowRight className="h-5 w-5 ml-2" />
                    </button>
                </div>

                <div className="mt-8 flex justify-center gap-8 text-sm opacity-80">
                    <div>
                        <span className="block text-2xl font-bold">50K+</span>
                        <span>Students</span>
                    </div>
                    <div className="border-l border-white/30" />
                    <div>
                        <span className="block text-2xl font-bold">200+</span>
                        <span>Schools</span>
                    </div>
                    <div className="border-l border-white/30" />
                    <div>
                        <span className="block text-2xl font-bold">95%</span>
                        <span>Offline Usage</span>
                    </div>
                </div>
            </div>
        </section>
    );
}
