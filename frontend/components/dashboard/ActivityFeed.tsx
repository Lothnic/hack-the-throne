"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Clock, MessageSquare } from "lucide-react";

function formatTimeAgo(timestamp: number) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

const avatarColors = [
    "from-amber-500/30 to-amber-600/10 text-amber-300",
    "from-teal-500/30 to-teal-600/10 text-teal-300",
    "from-rose-500/30 to-rose-600/10 text-rose-300",
    "from-violet-500/30 to-violet-600/10 text-violet-300",
    "from-sky-500/30 to-sky-600/10 text-sky-300",
];

function getAvatarColor(name: string) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return avatarColors[Math.abs(hash) % avatarColors.length];
}

export function ActivityFeed() {
    const conversations = useQuery(api.context.getRecentConversations, {
        limit: 10,
    });

    if (!conversations) {
        return (
            <div className="dashboard-card p-8 h-full">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                        <Clock className="w-4 h-4 text-amber-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-slate-200 font-outfit">
                        Recent Activity
                    </h2>
                </div>
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="animate-pulse flex gap-3">
                            <div className="w-10 h-10 rounded-full bg-white/[0.04]" />
                            <div className="flex-1 space-y-2">
                                <div className="h-3 bg-white/[0.04] rounded w-1/3" />
                                <div className="h-3 bg-white/[0.04] rounded w-2/3" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard-card p-8 h-full fade-in-up fade-in-delay-5">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Clock className="w-4 h-4 text-amber-400" />
                </div>
                <h2 className="text-xl font-semibold text-slate-200 font-outfit">
                    Recent Activity
                </h2>
            </div>

            {conversations.length === 0 ? (
                <div className="text-center py-12">
                    <MessageSquare className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 font-dm-sans">No conversations yet</p>
                    <p className="text-sm text-slate-600 mt-1 font-dm-sans">
                        Conversations will appear here
                    </p>
                </div>
            ) : (
                <div className="timeline-line space-y-1">
                    {conversations.slice(0, 6).map(
                        (
                            conv: {
                                _id: string;
                                speakerName: string;
                                timestamp: number;
                                transcript: string;
                                sentiment?: string;
                            },
                            index: number
                        ) => (
                            <div
                                key={conv._id}
                                className="group relative flex items-start gap-3 p-3 rounded-xl hover:bg-white/[0.03] transition-all duration-200 fade-in-up"
                                style={{ animationDelay: `${0.6 + index * 0.08}s` }}
                            >
                                {/* Avatar */}
                                <div
                                    className={`relative z-10 w-10 h-10 rounded-full bg-gradient-to-br ${getAvatarColor(
                                        conv.speakerName
                                    )} flex items-center justify-center font-outfit font-bold text-sm shrink-0`}
                                >
                                    {conv.speakerName[0]}
                                </div>

                                {/* Content */}
                                <div className="min-w-0 flex-1">
                                    <div className="flex items-center justify-between gap-2">
                                        <p className="font-semibold text-slate-200 truncate font-outfit text-sm">
                                            {conv.speakerName}
                                        </p>
                                        <div className="flex items-center gap-2 shrink-0">
                                            {conv.sentiment && (
                                                <span
                                                    className={`w-2 h-2 rounded-full ${conv.sentiment === "positive"
                                                            ? "bg-emerald-400"
                                                            : conv.sentiment === "negative"
                                                                ? "bg-rose-400"
                                                                : "bg-amber-400"
                                                        }`}
                                                    title={conv.sentiment}
                                                />
                                            )}
                                            <span className="text-xs text-slate-500 font-dm-sans">
                                                {formatTimeAgo(conv.timestamp)}
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-sm text-slate-400 line-clamp-2 mt-1 font-dm-sans leading-relaxed">
                                        {conv.transcript.length > 100
                                            ? conv.transcript.substring(0, 100) + "…"
                                            : conv.transcript}
                                    </p>
                                </div>
                            </div>
                        )
                    )}
                </div>
            )}
        </div>
    );
}
