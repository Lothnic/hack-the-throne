"use client";

import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Users } from "lucide-react";

export function PeopleGrid() {
    const speakers = useQuery(api.speakers.listSpeakers, {});

    if (!speakers) {
        return <div className="p-4 text-slate-400">Loading...</div>;
    }

    const knownPeople = speakers.filter((s: { name?: string }) => s.name && s.name !== "Unknown" && s.name !== "Unknown Person");

    return (
        <Card className="border-0 shadow-sm bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-xl text-slate-700">
                    <Users className="w-5 h-5 text-emerald-500" />
                    Your People
                </CardTitle>
            </CardHeader>
            <CardContent>
                {knownPeople.length === 0 ? (
                    <p className="text-center py-8 text-slate-400">No people recorded yet</p>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {knownPeople.map((person: { _id: string; name?: string; photoUrl?: string; relationship?: string }) => (
                            <div key={person._id} className="flex flex-col items-center p-4 rounded-2xl bg-gradient-to-b from-slate-50 to-white border border-slate-100 hover:border-emerald-200 transition-colors">
                                <Avatar className="h-20 w-20 mb-3 ring-4 ring-white shadow-md">
                                    <AvatarImage src={person.photoUrl} />
                                    <AvatarFallback className="text-2xl bg-emerald-100 text-emerald-600">
                                        {person.name?.[0]}
                                    </AvatarFallback>
                                </Avatar>
                                <h3 className="text-lg font-semibold text-slate-800">{person.name}</h3>
                                {person.relationship && (
                                    <span className="text-sm text-emerald-600 font-medium mt-1">
                                        {person.relationship}
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
