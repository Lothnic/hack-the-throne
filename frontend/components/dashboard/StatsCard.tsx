import { LucideIcon } from "lucide-react";

interface StatsCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color?: "amber" | "teal" | "rose" | "violet";
    delay?: number;
}

const colorConfig = {
    amber: {
        iconBg: "bg-amber-500/10",
        iconText: "text-amber-400",
        border: "accent-border-amber",
        gradient: "gradient-text-amber",
        glow: "rgba(245, 158, 11, 0.08)",
    },
    teal: {
        iconBg: "bg-teal-500/10",
        iconText: "text-teal-400",
        border: "accent-border-teal",
        gradient: "gradient-text-teal",
        glow: "rgba(20, 184, 166, 0.08)",
    },
    rose: {
        iconBg: "bg-rose-500/10",
        iconText: "text-rose-400",
        border: "accent-border-rose",
        gradient: "gradient-text-rose",
        glow: "rgba(244, 63, 94, 0.08)",
    },
    violet: {
        iconBg: "bg-violet-500/10",
        iconText: "text-violet-400",
        border: "accent-border-violet",
        gradient: "gradient-text-violet",
        glow: "rgba(139, 92, 246, 0.08)",
    },
};

export function StatsCard({ title, value, icon: Icon, color = "amber", delay = 0 }: StatsCardProps) {
    const cfg = colorConfig[color];

    return (
        <div
            className={`dashboard-card ${cfg.border} p-6 fade-in-up`}
            style={{
                animationDelay: `${delay * 0.1}s`,
                background: `linear-gradient(135deg, rgba(30, 30, 40, 0.7), rgba(30, 30, 40, 0.4))`,
            }}
        >
            <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl ${cfg.iconBg} flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${cfg.iconText}`} />
                </div>
                <p className="text-sm font-medium text-slate-400 uppercase tracking-widest font-dm-sans">
                    {title}
                </p>
            </div>
            <h3 className={`text-4xl font-bold font-outfit ${cfg.gradient} shimmer-text`}>
                {value}
            </h3>
        </div>
    );
}
