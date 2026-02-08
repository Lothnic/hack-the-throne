"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock } from "lucide-react";

function formatTimeAgo(timestamp: number) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

export function ActivityFeed() {
    const conversations = useQuery(api.context.getRecentConversations, { limit: 10 });

    if (!conversations) {
        return <div className="p-4 text-slate-400">Loading...</div>;
    }

    return (
        <Card className="border-0 shadow-sm bg-white/80 backdrop-blur-sm h-full">
            <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-xl text-slate-700">
                    <Clock className="w-5 h-5 text-sky-500" />
                    Recent Activity
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
                {conversations.length === 0 ? (
                    <p className="text-center py-8 text-slate-400">No conversations yet</p>
                ) : (
                    conversations.slice(0, 6).map((conv: { _id: string; speakerName: string; timestamp: number; transcript: string }) => (
                        <div key={conv._id} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 hover:bg-sky-50 transition-colors">
                            <div className="w-10 h-10 rounded-full bg-sky-100 flex items-center justify-center text-sky-600 font-bold shrink-0">
                                {conv.speakerName[0]}
                            </div>
                            <div className="min-w-0 flex-1">
                                <div className="flex items-center justify-between gap-2">
                                    <p className="font-semibold text-slate-700 truncate">{conv.speakerName}</p>
                                    <span className="text-xs text-slate-400 shrink-0">{formatTimeAgo(conv.timestamp)}</span>
                                </div>
                                <p className="text-sm text-slate-500 line-clamp-2 mt-0.5">
                                    {conv.transcript.substring(0, 80)}...
                                </p>
                            </div>
                        </div>
                    ))
                )}
            </CardContent>
        </Card>
    );
}
