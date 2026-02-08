import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color?: "sky" | "emerald" | "rose" | "amber";
}

const colorStyles = {
    sky: "bg-sky-100 text-sky-600",
    emerald: "bg-emerald-100 text-emerald-600",
    rose: "bg-rose-100 text-rose-600",
    amber: "bg-amber-100 text-amber-600",
};

export function StatsCard({ title, value, icon: Icon, color = "sky" }: StatsCardProps) {
    return (
        <Card className="border-0 shadow-sm bg-white/80 backdrop-blur-sm">
            <CardContent className="p-6">
                <div className={`w-12 h-12 rounded-xl ${colorStyles[color]} flex items-center justify-center mb-4`}>
                    <Icon className="w-6 h-6" />
                </div>
                <p className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</p>
                <h3 className="text-3xl font-bold text-slate-800 mt-1">{value}</h3>
            </CardContent>
        </Card>
    );
}
