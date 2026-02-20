"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Users, Eye, Clock } from "lucide-react";

function formatLastSeen(timestamp: number) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

export function PeopleGrid() {
    const speakers = useQuery(api.speakers.listSpeakers, {});

    if (!speakers) {
        return (
            <div className="dashboard-card p-8">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
                        <Users className="w-4 h-4 text-teal-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-slate-200 font-outfit">Your People</h2>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="animate-pulse rounded-2xl bg-white/[0.03] h-48" />
                    ))}
                </div>
            </div>
        );
    }

    const knownPeople = speakers.filter(
        (s: { name?: string }) => s.name && s.name !== "Unknown" && s.name !== "Unknown Person"
    );

    return (
        <div className="dashboard-card p-8 fade-in-up fade-in-delay-4">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center">
                    <Users className="w-4 h-4 text-teal-400" />
                </div>
                <h2 className="text-xl font-semibold text-slate-200 font-outfit">Your People</h2>
                {knownPeople.length > 0 && (
                    <span className="ml-auto text-xs font-medium text-slate-500 bg-white/[0.04] px-2.5 py-1 rounded-full">
                        {knownPeople.length} known
                    </span>
                )}
            </div>

            {knownPeople.length === 0 ? (
                <div className="text-center py-12">
                    <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 font-dm-sans">No people recorded yet</p>
                    <p className="text-sm text-slate-600 mt-1 font-dm-sans">People will appear here when recognized</p>
                </div>
            ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {knownPeople.map(
                        (
                            person: {
                                _id: string;
                                name?: string;
                                photoUrl?: string;
                                relationship?: string;
                                lastSeen?: number;
                                seenCount?: number;
                            },
                            index: number
                        ) => (
                            <div
                                key={person._id}
                                className="group flex flex-col items-center p-5 rounded-2xl bg-white/[0.03] border border-white/[0.04] hover:border-teal-500/20 hover:bg-white/[0.06] transition-all duration-300 cursor-default fade-in-up"
                                style={{ animationDelay: `${0.5 + index * 0.08}s` }}
                            >
                                <Avatar className="h-20 w-20 mb-4 avatar-ring-teal transition-shadow duration-300 group-hover:shadow-[0_0_0_3px_rgba(20,184,166,0.5),0_0_20px_rgba(20,184,166,0.2)]">
                                    <AvatarImage src={person.photoUrl} />
                                    <AvatarFallback className="text-2xl bg-gradient-to-br from-teal-500/20 to-teal-600/10 text-teal-300 font-outfit font-semibold">
                                        {person.name?.[0]}
                                    </AvatarFallback>
                                </Avatar>

                                <h3 className="text-lg font-semibold text-slate-100 font-outfit">
                                    {person.name}
                                </h3>

                                {person.relationship && (
                                    <span className="mt-2 text-xs font-medium text-teal-300 bg-teal-500/10 px-3 py-1 rounded-full border border-teal-500/20">
                                        {person.relationship}
                                    </span>
                                )}

                                <div className="flex items-center gap-3 mt-3 text-xs text-slate-500 font-dm-sans">
                                    {person.seenCount && (
                                        <span className="flex items-center gap-1">
                                            <Eye className="w-3 h-3" />
                                            {person.seenCount}
                                        </span>
                                    )}
                                    {person.lastSeen && (
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {formatLastSeen(person.lastSeen)}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )
                    )}
                </div>
            )}
        </div>
    );
}
