"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Search, Globe, Brain, Sparkles, ArrowRight, Loader2 } from "lucide-react"

export default function AnalyzePage() {
    const [url, setUrl] = useState("")
    const [questions, setQuestions] = useState("")
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()

    const handleAnalyze = async () => {
        if (!url.trim()) return

        setIsAnalyzing(true)
        setError(null)
        try {
            const qs = questions
                .split("\n")
                .map((q) => q.trim())
                .filter(Boolean)

            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, questions: qs }),
            })
            const data = await res.json().catch(() => ({}))
            if (!res.ok) {
                throw new Error(data?.detail || data?.error || "Analyze request failed")
            }
            // After successful analyze, navigate to sessions list
            router.push(`/sessions/${data.id}`)
        } catch (e: any) {
            setError(e?.message || "Unexpected error")
        } finally {
            setIsAnalyzing(false)
        }
    }

    const exampleQuestions = [
        "What industry is this company in?",
        "What is the company size?",
        "What products or services do they offer?",
        "Who is their target audience?",
        "What is their business model?",
    ]

    type SessionSummary = {
        id: string
        url: string
        created_at: string
        ai_provider?: string
        model?: string
        status: string
    }

    type RecentItem = { url: string; industry: string; date: string; id: string }

    const [recentAnalyses, setRecentAnalyses] = useState<RecentItem[]>([])

    const formatRelative = (iso: string) => {
        const d = new Date(iso)
        const now = new Date()
        const diffMs = now.getTime() - d.getTime()
        const minutes = Math.floor(diffMs / 60000)
        if (minutes < 1) return "just now"
        if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`
        const hours = Math.floor(minutes / 60)
        if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`
        const days = Math.floor(hours / 24)
        return `${days} day${days === 1 ? "" : "s"} ago`
    }

    useEffect(() => {
        let cancelled = false
            ; (async () => {
                try {
                    const res = await fetch("/api/analyze/sessions", { cache: "no-store" })
                    if (!res.ok) return
                    const sessions: SessionSummary[] = await res.json()
                    if (cancelled) return
                    const top = sessions.slice(0, 3).map((s) => ({
                        url: s.url,
                        industry: s.model || s.ai_provider || "",
                        date: formatRelative(s.created_at),
                        id: s.id,
                    }))
                    setRecentAnalyses(top)
                } catch { }
            })()
        return () => {
            cancelled = true
        }
    }, [])

    return (
        <div className="relative">
            {/* Grid pattern overlay */}
            <div className="absolute inset-0 grid-pattern opacity-10" />

            <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Header */}
                <div className="text-center mb-12">
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                            <Search className="w-6 h-6 text-primary" />
                        </div>
                    </div>

                    <h1 className="text-3xl md:text-4xl font-bold mb-4">Analyze a Website</h1>

                    <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                        Enter a website URL and optional questions to get AI-powered insights about the business, industry, and
                        more.
                    </p>
                </div>

                {/* Main Analysis Form */}
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm mb-8">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Globe className="w-5 h-5 text-primary" />
                            Website Analysis
                        </CardTitle>
                        <CardDescription>Provide a website URL and any specific questions you'd like answered</CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-6">
                        {error && (
                            <div className="text-sm text-red-600">{error}</div>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="url" className="text-sm font-medium">
                                Website URL *
                            </Label>
                            <Input
                                id="url"
                                type="url"
                                placeholder="https://example.com"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                className="bg-background/50"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="questions" className="text-sm font-medium">
                                Questions (Optional)
                            </Label>
                            <Textarea
                                id="questions"
                                placeholder="What industry is this company in? What is their target market?"
                                value={questions}
                                onChange={(e) => setQuestions(e.target.value)}
                                rows={4}
                                className="bg-background/50 resize-none"
                            />
                            <p className="text-xs text-muted-foreground">
                                Leave empty for default analysis, or ask specific questions about the website
                            </p>
                        </div>

                        <Button
                            onClick={handleAnalyze}
                            disabled={!url.trim() || isAnalyzing}
                            size="lg"
                            className="w-full bg-primary hover:bg-primary/90"
                        >
                            {isAnalyzing ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Analyzing Website...
                                </>
                            ) : (
                                <>
                                    <Brain className="w-4 h-4 mr-2" />
                                    Analyze Website
                                    <ArrowRight className="w-4 h-4 ml-2" />
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                <div className="grid md:grid-cols-2 gap-6">
                    {/* Example Questions */}
                    <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <Sparkles className="w-5 h-5 text-primary" />
                                Example Questions
                            </CardTitle>
                            <CardDescription>Get inspired by these common analysis questions</CardDescription>
                        </CardHeader>

                        <CardContent>
                            <div className="space-y-3">
                                {exampleQuestions.map((question, index) => (
                                    <div
                                        key={index}
                                        className="p-3 rounded-lg bg-background/50 border border-border/50 cursor-pointer hover:bg-background/70 transition-colors"
                                        onClick={() => setQuestions((prev) => (prev ? `${prev}\n${question}` : question))}
                                    >
                                        <p className="text-sm">{question}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Recent Analyses */}
                    <Card className="border-border/50 bg-card/30 backdrop-blur-sm">
                        <CardHeader>
                            <CardTitle className="text-lg">Recent Analyses</CardTitle>
                            <CardDescription>Your recently analyzed websites</CardDescription>
                        </CardHeader>

                        <CardContent>
                            <div className="space-y-4">
                                {recentAnalyses.map((analysis, index) => (
                                    <div
                                        key={index}
                                        className="flex items-center justify-between p-3 rounded-lg bg-background/50 border border-border/50"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{analysis.url}</p>
                                            <div className="flex items-center gap-2 mt-1">
                                                {/* <Badge variant="secondary" className="text-xs">
                                                    {analysis.industry}
                                                </Badge> */}
                                                <span className="text-xs text-muted-foreground">{analysis.date}</span>
                                            </div>
                                        </div>
                                        <Button onClick={() => router.push(`/sessions/${analysis.id}`)} variant="ghost" size="sm">
                                            <ArrowRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                ))}
                            </div>

                            <Separator className="my-4" />

                            <Button onClick={() => router.push("/sessions")} variant="outline" size="sm" className="w-full bg-transparent">
                                View All Sessions
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}


