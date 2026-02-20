"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { PeopleGrid } from "@/components/dashboard/PeopleGrid";
import { Users, MessageSquare, Clock, Heart, ArrowLeft, Activity } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
    const speakers = useQuery(api.speakers.listSpeakers, {});
    const conversations = useQuery(api.context.getRecentConversations, { limit: 100 });

    const totalInteractions = conversations?.length || 0;
    const knownPeopleCount =
        speakers?.filter(
            (s: { name?: string }) =>
                s.name && s.name !== "Unknown" && s.name !== "Unknown Person"
        ).length || 0;

    const totalMinutes =
        speakers?.reduce(
            (acc: number, curr: { totalSpeakingTime?: number }) =>
                acc + (curr.totalSpeakingTime || 0),
            0
        ) || 0;
    const totalHours = Math.round(totalMinutes / 60);

    return (
        <div className="min-h-screen bg-[#0c0c14] font-dm-sans">
            {/* Ambient background blobs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-amber-500/[0.03] blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-5%] w-[40vw] h-[40vw] rounded-full bg-teal-500/[0.03] blur-[100px]" />
                <div className="absolute top-[40%] right-[20%] w-[30vw] h-[30vw] rounded-full bg-violet-500/[0.02] blur-[80px]" />
            </div>

            {/* Content */}
            <div className="relative z-10 max-w-6xl mx-auto px-6 py-10 space-y-10">
                {/* Header */}
                <div className="flex items-center justify-between fade-in-up">
                    <div className="flex items-center gap-4">
                        <div>
                            <div className="flex items-center gap-3">
                                <h1 className="text-4xl font-bold text-white tracking-tight font-outfit">
                                    Memory Dashboard
                                </h1>
                                <div className="status-dot mt-1" title="System active" />
                            </div>
                            <p className="text-base text-slate-400 mt-1.5 font-dm-sans">
                                People who care about you · Always remembered
                            </p>
                        </div>
                    </div>
                    <Link
                        href="/"
                        className="group flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.06] text-slate-300 hover:text-white hover:bg-white/[0.08] hover:border-white/[0.1] transition-all duration-300 font-dm-sans text-sm"
                    >
                        <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
                        Back to Camera
                    </Link>
                </div>

                {/* Stats Row */}
                <div className="grid gap-5 grid-cols-2 lg:grid-cols-4 ambient-glow">
                    <StatsCard
                        title="Conversations"
                        value={totalInteractions.toString()}
                        icon={MessageSquare}
                        color="amber"
                        delay={1}
                    />
                    <StatsCard
                        title="People"
                        value={knownPeopleCount.toString()}
                        icon={Users}
                        color="teal"
                        delay={2}
                    />
                    <StatsCard
                        title="Time Together"
                        value={`${totalHours}h`}
                        icon={Heart}
                        color="rose"
                        delay={3}
                    />
                    <StatsCard
                        title="Last Visit"
                        value={
                            conversations?.[0]
                                ? new Date(conversations[0].timestamp).toLocaleTimeString(
                                    [],
                                    { hour: "2-digit", minute: "2-digit" }
                                )
                                : "—"
                        }
                        icon={Clock}
                        color="violet"
                        delay={4}
                    />
                </div>

                {/* Main Content */}
                <div className="grid gap-8 lg:grid-cols-3">
                    <div className="lg:col-span-2">
                        <PeopleGrid />
                    </div>
                    <div>
                        <ActivityFeed />
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-center gap-2 py-4 fade-in-up fade-in-delay-6">
                    <Activity className="w-3.5 h-3.5 text-slate-600" />
                    <p className="text-xs text-slate-600 font-dm-sans">
                        ForgetMeNot · AI Memory Companion
                    </p>
                </div>
            </div>
        </div>
    );
}
