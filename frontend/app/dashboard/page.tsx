"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { PeopleGrid } from "@/components/dashboard/PeopleGrid";
import { Users, MessageSquare, Clock, Heart } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export default function DashboardPage() {
    const speakers = useQuery(api.speakers.listSpeakers, {});
    const conversations = useQuery(api.context.getRecentConversations, { limit: 100 });

    const totalInteractions = conversations?.length || 0;
    const knownPeopleCount = speakers?.filter((s: { name?: string }) => s.name && s.name !== "Unknown" && s.name !== "Unknown Person").length || 0;

    const totalMinutes = speakers?.reduce((acc: number, curr: { totalSpeakingTime?: number }) => acc + (curr.totalSpeakingTime || 0), 0) || 0;
    const totalHours = Math.round(totalMinutes / 60);

    return (
        <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-emerald-50 p-8">
            <div className="max-w-6xl mx-auto space-y-10">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-slate-800 tracking-tight">Memory Dashboard</h1>
                        <p className="text-lg text-slate-500 mt-1">People who care about you</p>
                    </div>
                    <Link href="/">
                        <Button variant="outline" size="lg" className="gap-2 text-base">
                            <ArrowLeft className="w-5 h-5" />
                            Back to Camera
                        </Button>
                    </Link>
                </div>

                {/* Stats Row */}
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                    <StatsCard
                        title="Conversations"
                        value={totalInteractions.toString()}
                        icon={MessageSquare}
                        color="sky"
                    />
                    <StatsCard
                        title="People"
                        value={knownPeopleCount.toString()}
                        icon={Users}
                        color="emerald"
                    />
                    <StatsCard
                        title="Time Together"
                        value={`${totalHours}h`}
                        icon={Heart}
                        color="rose"
                    />
                    <StatsCard
                        title="Last Visit"
                        value={conversations?.[0] ? new Date(conversations[0].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "—"}
                        icon={Clock}
                        color="amber"
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
            </div>
        </div>
    );
}
