import React from "react";
import { Button } from "@/components/ui/button";
import { Play, Smartphone, WifiOff } from "lucide-react";

export function HeroSection() {
    return (
        <section className="relative overflow-hidden bg-gradient-hero py-16 md:py-24">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-20 right-10 w-64 h-64 bg-accent/10 rounded-full blur-3xl" />
                <div className="absolute bottom-20 left-10 w-48 h-48 bg-primary/10 rounded-full blur-3xl" />
            </div>

            <div className="container relative">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    {/* Content */}
                    <div className="animate-fade-in">
                        <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                            </span>
                            SIH 2025 Project
                        </div>

                        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-6">
                            <span className="text-gradient-teal">Utkal Quest:</span>
                            <br />
                            <span className="text-foreground">AI-Driven Gamified</span>
                            <br />
                            <span className="text-gradient-sunrise">Mastery</span>
                        </h1>

                        <p className="text-lg text-muted-foreground mb-8 max-w-lg">
                            Empowering rural students in Odisha with offline-first, gamified STEM learning.
                            Build mathematical intuition through quests, not just formulas.
                        </p>

                        <div className="flex flex-wrap gap-4 mb-8">
                            <Button size="lg" className="bg-gradient-teal hover:opacity-90 shadow-soft">
                                <Play className="h-5 w-5 mr-2" />
                                Start Your Quest
                            </Button>
                            <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/5">
                                <Smartphone className="h-5 w-5 mr-2" />
                                Download App
                            </Button>
                        </div>

                        {/* Key Features Pills */}
                        <div className="flex flex-wrap gap-3">
                            <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full shadow-card text-sm">
                                <WifiOff className="h-4 w-4 text-primary" />
                                <span className="text-muted-foreground">Works Offline</span>
                            </div>
                            <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full shadow-card text-sm">
                                <span className="text-accent">🏆</span>
                                <span className="text-muted-foreground">Gamified Learning</span>
                            </div>
                            <div className="flex items-center gap-2 bg-card px-4 py-2 rounded-full shadow-card text-sm">
                                <span className="text-primary">🧠</span>
                                <span className="text-muted-foreground">AI-Powered</span>
                            </div>
                        </div>
                    </div>

                    {/* Visual - Quest Preview */}
                    <div className="relative animate-slide-up">
                        <div className="bg-card rounded-2xl shadow-elevated p-6 border border-border">
                            {/* Quest Header */}
                            <div className="flex items-center justify-between mb-6">
                                <div>
                                    <p className="text-sm text-muted-foreground">Current Quest</p>
                                    <h3 className="text-xl font-semibold">Algebra Foundations</h3>
                                </div>
                                <div className="flex items-center gap-2 text-accent">
                                    <span className="text-2xl">⭐</span>
                                    <span className="font-bold">1,250 XP</span>
                                </div>
                            </div>

                            {/* Progress */}
                            <div className="mb-6">
                                <div className="flex justify-between text-sm mb-2">
                                    <span className="text-muted-foreground">Level 5/12</span>
                                    <span className="font-medium text-primary">42%</span>
                                </div>
                                <div className="h-3 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-sunrise rounded-full transition-all duration-500"
                                        style={{ width: '42%' }}
                                    />
                                </div>
                            </div>

                            {/* Intuition Profile Preview */}
                            <div className="grid grid-cols-2 gap-3 mb-6">
                                {[
                                    { label: "Procedural", value: 78, color: "bg-[#0ea5e9]" },
                                    { label: "Conceptual", value: 65, color: "bg-[#8b5cf6]" },
                                    { label: "Strategic", value: 82, color: "bg-[#f59e0b]" },
                                    { label: "Adaptive", value: 71, color: "bg-[#10b981]" },
                                ].map((stat) => (
                                    <div key={stat.label} className="bg-muted/50 rounded-lg p-3">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs text-muted-foreground">{stat.label}</span>
                                            <span className="text-xs font-medium">{stat.value}%</span>
                                        </div>
                                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${stat.color} rounded-full`}
                                                style={{ width: `${stat.value}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* CTA */}
                            <Button className="w-full bg-gradient-teal hover:opacity-90">
                                Continue Quest →
                            </Button>
                        </div>

                        {/* Floating badges */}
                        <div className="absolute -top-4 -right-4 bg-accent text-accent-foreground px-4 py-2 rounded-full shadow-lg text-sm font-medium animate-float">
                            🔥 3-Day Streak!
                        </div>
                        <div className="absolute -bottom-4 -left-4 bg-[#10b981] text-white px-4 py-2 rounded-full shadow-lg text-sm font-medium">
                            ✓ Badge Earned
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
