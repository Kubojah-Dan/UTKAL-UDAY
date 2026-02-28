import React from "react";
import {
    WifiOff,
    Brain,
    Trophy,
    Users,
    BarChart3,
    Smartphone,
    Zap,
    Target
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
    {
        icon: WifiOff,
        title: "Offline-First Learning",
        description: "Complete quests without internet. Sync when you reach a network zone. Perfect for rural connectivity.",
        color: "text-primary",
        bgColor: "bg-primary/10",
    },
    {
        icon: Brain,
        title: "AI-Powered Personalization",
        description: "Bayesian Knowledge Tracing adapts to your learning pace. The AI knows what you need to learn next.",
        color: "text-[#8b5cf6]",
        bgColor: "bg-[#8b5cf6]/10",
    },
    {
        icon: Trophy,
        title: "Gamified Quests",
        description: "Earn XP, unlock badges, and level up. Learning becomes an adventure, not a chore.",
        color: "text-accent",
        bgColor: "bg-accent/10",
    },
    {
        icon: Target,
        title: "Mathematical Intuition",
        description: "We measure not just correctness, but HOW you solve. Build true understanding, not rote memory.",
        color: "text-[#f59e0b]",
        bgColor: "bg-[#f59e0b]/10",
    },
    {
        icon: Users,
        title: "Bluetooth Battles",
        description: "Challenge friends via Bluetooth—no internet needed. Turn learning into a social experience.",
        color: "text-[#0ea5e9]",
        bgColor: "bg-[#0ea5e9]/10",
    },
    {
        icon: BarChart3,
        title: "Teacher Analytics",
        description: "Explainable AI shows teachers exactly WHY a student struggles, not just that they do.",
        color: "text-[#ef4444]",
        bgColor: "bg-[#ef4444]/10",
    },
    {
        icon: Smartphone,
        title: "Budget Phone Ready",
        description: "Runs smoothly on ₹5,000 phones with 2GB RAM. No expensive hardware needed.",
        color: "text-[#10b981]",
        bgColor: "bg-[#10b981]/10",
    },
    {
        icon: Zap,
        title: "Odia Language Support",
        description: "Full Odia (ଓଡ଼ିଆ) interface and content. Learn in your mother tongue.",
        color: "text-[#14b8a6]",
        bgColor: "bg-[#14b8a6]/10",
    },
];

export function FeaturesSection() {
    return (
        <section className="py-16 md:py-24 bg-background">
            <div className="container">
                <div className="text-center mb-12">
                    <h2 className="text-3xl md:text-4xl font-bold mb-4">
                        <span className="text-gradient-teal">Built for Rural India</span>
                    </h2>
                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                        Every feature designed with connectivity constraints, hardware limitations, and local context in mind.
                    </p>
                </div>

                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {features.map((feature, index) => (
                        <Card
                            key={feature.title}
                            className="border-border/50 shadow-card hover:shadow-elevated transition-shadow duration-300 group"
                            style={{ animationDelay: `${index * 100}ms` }}
                        >
                            <CardHeader className="pb-3">
                                <div className={`w-12 h-12 rounded-xl ${feature.bgColor} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                                    <feature.icon className={`h-6 w-6 ${feature.color}`} />
                                </div>
                                <CardTitle className="text-lg">{feature.title}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-sm text-muted-foreground">{feature.description}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        </section>
    );
}
