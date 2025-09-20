"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { History, Search, ExternalLink, MessageSquare, Calendar, Filter, Plus } from "lucide-react"

export default function SessionsPage() {
    const [searchQuery, setSearchQuery] = useState("")
    const [error, setError] = useState<string | null>(null)

    type Session = {
        id: string
        url: string
        created_at: string
        ai_provider?: string
        model?: string
        status: string
    }

    const [sessions, setSessions] = useState<Session[]>([])

    useEffect(() => {
        let cancelled = false
            ; (async () => {
                try {
                    const res = await fetch("/api/analyze/sessions", { cache: "no-store" })
                    if (!res.ok) throw new Error("Failed to load sessions")
                    const data = (await res.json()) as Session[]
                    if (!cancelled) setSessions(data)
                } catch (e: any) {
                    if (!cancelled) setError(e?.message || "Failed to load sessions")
                }
            })()
        return () => {
            cancelled = true
        }
    }, [])

    const filteredSessions = useMemo(() => {
        const q = searchQuery.toLowerCase()
        return sessions.filter((session) =>
            session.url.toLowerCase().includes(q) ||
            (session.ai_provider || "").toLowerCase().includes(q) ||
            (session.model || "").toLowerCase().includes(q) ||
            (session.status || "").toLowerCase().includes(q),
        )
    }, [sessions, searchQuery])

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })
    }

    return (
        <div className="relative">
            {/* Grid pattern overlay */}
            <div className="absolute inset-0 grid-pattern opacity-10" />

            <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                            <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
                                <History className="w-5 h-5 text-primary" />
                            </div>
                            Analysis Sessions
                        </h1>
                        <p className="text-muted-foreground">View and manage all your website analysis sessions</p>
                    </div>

                    <Button asChild className="bg-primary hover:bg-primary/90">
                        <Link href="/analyze" className="gap-2">
                            <Plus className="w-4 h-4" />
                            New Analysis
                        </Link>
                    </Button>
                </div>

                {/* Search and Filters */}
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm mb-6">
                    <CardContent className="p-4">
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search sessions by URL, provider, model, or status..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-10 bg-background/50"
                                />
                            </div>

                            <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                                <Filter className="w-4 h-4" />
                                Filter
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Error */}
                {error && (
                    <Card className="border-border/50 bg-card/30 backdrop-blur-sm mb-4">
                        <CardContent className="p-4 text-sm text-red-600">{error}</CardContent>
                    </Card>
                )}

                {/* Sessions List */}
                <div className="space-y-4">
                    {filteredSessions.length === 0 ? (
                        <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
                            <CardContent className="p-12 text-center">
                                <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <History className="w-8 h-8 text-muted-foreground" />
                                </div>
                                <h3 className="text-lg font-medium mb-2">No sessions found</h3>
                                <p className="text-muted-foreground mb-4">
                                    {searchQuery ? "Try adjusting your search terms" : "Start by analyzing your first website"}
                                </p>
                                <Button asChild>
                                    <Link href="/analyze">Analyze Website</Link>
                                </Button>
                            </CardContent>
                        </Card>
                    ) : (
                        filteredSessions.map((session) => {
                            let host = session.url
                            try {
                                host = new URL(session.url).hostname
                            } catch { }
                            return (
                                <Card
                                    key={session.id}
                                    className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/70 transition-colors"
                                >
                                    <CardContent className="p-6">
                                        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start gap-3 mb-3">
                                                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                                                        <ExternalLink className="w-5 h-5 text-primary" />
                                                    </div>

                                                    <div className="flex-1 min-w-0">
                                                        <h3 className="font-semibold text-lg mb-1 truncate">{host}</h3>
                                                        <p className="text-sm text-muted-foreground mb-2 truncate">{session.url}</p>

                                                        <div className="flex items-center gap-2 mb-3">
                                                            {session.status && (
                                                                <Badge variant="secondary" className="text-xs">
                                                                    {session.status}
                                                                </Badge>
                                                            )}
                                                            {/* {(session.model || session.ai_provider) && (
                                                                <Badge variant="outline" className="text-xs">
                                                                    {session.model || session.ai_provider}
                                                                </Badge>
                                                            )} */}
                                                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                                <Calendar className="w-3 h-3" />
                                                                {formatDate(session.created_at)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                <Button variant="outline" size="sm" asChild>
                                                    <Link href={session.url} target="_blank" className="gap-2">
                                                        <ExternalLink className="w-4 h-4" />
                                                        Visit
                                                    </Link>
                                                </Button>

                                                <Button size="sm" asChild className="bg-primary hover:bg-primary/90">
                                                    <Link href={`/sessions/${session.id}`}>View Details</Link>
                                                </Button>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            )
                        })
                    )}
                </div>

                {/* Stats */}
                {filteredSessions.length > 0 && (
                    <div className="mt-8 pt-6 border-t border-border/50">
                        <div className="flex items-center justify-between text-sm text-muted-foreground">
                            <span>
                                Showing {filteredSessions.length} of {sessions.length} sessions
                            </span>
                            <span>Total analyses: {sessions.length}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

