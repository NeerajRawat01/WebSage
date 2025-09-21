"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ArrowLeft, ExternalLink, Send, Copy, Check, User, Bot } from "lucide-react"

export default function SessionDetailsPage() {
    const params = useParams()
    const [followUpQuestion, setFollowUpQuestion] = useState("")
    const [isAsking, setIsAsking] = useState(false)
    const [copiedSection, setCopiedSection] = useState<string | null>(null)
    const [loadError, setLoadError] = useState<string | null>(null)

    type SessionSummary = {
        id: string
        url: string
        created_at: string
        ai_provider?: string
        model?: string
        status: string
    }

    type ConverseResponse = {
        url: string
        user_query: string
        agent_response: string
        context_sources: string[]
    }

    type ConversationMessage = {
        id: string
        type: "user" | "assistant"
        message: string
        timestamp: string
    }

    const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null)
    const [analysis, setAnalysis] = useState<ConverseResponse | null>(null)
    const [conversation, setConversation] = useState<ConversationMessage[]>([])
    type QAItem = { question: string; answer: string }
    type AnalyzeDetail = {
        url: string
        analysis_timestamp: string
        company_info: {
            industry?: string | null
            company_size?: string | null
            location?: string | null
            core_products_services?: string[] | null
            unique_selling_proposition?: string | null
            target_audience?: string | null
            contact_info?: {
                email?: string | null
                phone?: string | null
                social_media?: Record<string, string | null> | null
            } | null
        }
        extracted_answers: QAItem[]
    }
    const [detail, setDetail] = useState<AnalyzeDetail | null>(null)

    useEffect(() => {
        let cancelled = false
        setLoadError(null)
            ; (async () => {
                try {
                    const res = await fetch("/api/analyze/sessions", { cache: "no-store" })
                    if (!res.ok) throw new Error("Failed to load sessions")
                    const data: SessionSummary[] = await res.json()
                    if (cancelled) return
                    const found = data.find((s) => s.id === params?.id) || null
                    if (!found) throw new Error("Session not found")
                    setSessionSummary(found)
                    // Load detailed analysis for insights and extracted answers
                    const dr = await fetch(`/api/analyze/sessions/${params?.id}`, { cache: "no-store" })
                    if (dr.ok) {
                        const d: AnalyzeDetail = await dr.json()
                        if (!cancelled) {
                            setDetail(d)
                        }
                    }
                    // Load conversation history for this session
                    const hr = await fetch(`/api/converse/history/${params?.id}`, { cache: "no-store" })
                    if (hr.ok) {
                        const hist: Array<{ user_query: string; agent_response: string; created_at: string }> = await hr.json()
                        if (!cancelled) {
                            const conv: ConversationMessage[] = []
                            for (const h of hist) {
                                conv.push({ id: `${h.created_at}-u`, type: "user", message: h.user_query, timestamp: h.created_at })
                                conv.push({ id: `${h.created_at}-a`, type: "assistant", message: h.agent_response, timestamp: h.created_at })
                            }
                            setConversation(conv)
                        }
                    }
                } catch (e: any) {
                    if (!cancelled) setLoadError(e?.message || "Failed to load session")
                }
            })()
        return () => {
            cancelled = true
        }
    }, [params?.id])

    const handleAskFollowUp = async () => {
        if (!followUpQuestion.trim()) return

        setIsAsking(true)
        const userMsg: ConversationMessage = {
            id: `${Date.now()}-u`,
            type: "user",
            message: followUpQuestion,
            timestamp: new Date().toISOString(),
        }
        setConversation((prev) => [...prev, userMsg])
        try {
            const res = await fetch("/api/converse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: params?.id, query: followUpQuestion }),
            })
            const data: ConverseResponse = await res.json()
            if (!res.ok) throw new Error((data as any)?.detail || (data as any)?.error || "Request failed")
            setAnalysis(data)
            const aiMsg: ConversationMessage = {
                id: `${Date.now()}-a`,
                type: "assistant",
                message: data.agent_response,
                timestamp: new Date().toISOString(),
            }
            setConversation((prev) => [...prev, aiMsg])
        } catch (e: any) {
            const aiMsg: ConversationMessage = {
                id: `${Date.now()}-e`,
                type: "assistant",
                message: e?.message || "Unexpected error",
                timestamp: new Date().toISOString(),
            }
            setConversation((prev) => [...prev, aiMsg])
        } finally {
            setIsAsking(false)
            setFollowUpQuestion("")
        }
    }

    const copyToClipboard = async (text: string, section: string) => {
        await navigator.clipboard.writeText(text)
        setCopiedSection(section)
        setTimeout(() => setCopiedSection(null), 2000)
    }

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


    const sessionTitle = useMemo(() => {
        if (sessionSummary?.url) {
            try {
                const u = new URL(sessionSummary.url)
                return u.hostname
            } catch {
                return sessionSummary.url
            }
        }
        return "Session"
    }, [sessionSummary])

    const sessionData = useMemo(() => {
        return {
            session: {
                id: params?.id,
                url: analysis?.url || detail?.url || sessionSummary?.url || "-",
                created_at: sessionSummary?.created_at ? formatDate(sessionSummary.created_at) : "-",
                status: sessionSummary?.status || "-",
                // model: sessionSummary?.model || "-",
                // ai_provider: sessionSummary?.ai_provider || "-",
            },
            query: {
                original_query:
                    analysis?.user_query ||
                    detail?.extracted_answers?.[0]?.question ||
                    (conversation.find((m) => m.type === "user")?.message ?? "-"),
                ai_response:
                    analysis?.agent_response ||
                    detail?.extracted_answers?.[0]?.answer ||
                    "Ask a question below to see the analysis.",
                context_sources: analysis?.context_sources || [],
            },
            company_insights: {
                industry: detail?.company_info?.industry || "Not available",
                company_size: detail?.company_info?.company_size || "Not available",
                target_audience: detail?.company_info?.target_audience || "Not available",
                business_model: detail?.company_info?.unique_selling_proposition || "Not available",
                core_products_services: detail?.company_info?.core_products_services || [],
                location: detail?.company_info?.location || "Not available",
                contact_info: detail?.company_info?.contact_info || {},
            },
            extracted_qa: detail?.extracted_answers || [],
            conversation_history: conversation,
        }
    }, [sessionSummary, analysis, detail, conversation, params?.id])

    return (
        <div className="grid grid-cols-1 mx-auto gap-6 px-4 sm:px-6 lg:px-8 py-8 max-w-6xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <Button variant="outline" size="sm" asChild>
                        <Link href="/sessions" className="gap-2">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Sessions
                        </Link>
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold">{sessionTitle}</h1>
                        <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-xs">
                                {sessionData.session.status}
                            </Badge>
                            {/* {sessionData.session.model !== "-" && (
                                <Badge variant="outline" className="text-xs">
                                    {sessionData.session.model}
                                </Badge>
                            )} */}
                        </div>
                    </div>
                </div>
                <Button variant="outline" size="sm" asChild>
                    <Link href={sessionData.session.url} target="_blank" className="gap-2">
                        <ExternalLink className="w-4 h-4" />
                        Visit Site
                    </Link>
                </Button>
            </div>

            {loadError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">{loadError}</div>
            )}

            {/* Session Data */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Session Data</CardTitle>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(JSON.stringify(sessionData.session, null, 2), "session")}
                    >
                        {copiedSection === "session" ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="bg-muted/50 p-4 rounded-lg font-mono text-sm overflow-x-auto text-foreground">
                        <pre>{JSON.stringify(sessionData.session, null, 2)}</pre>
                    </div>
                </CardContent>
            </Card>

            {/* Query & Response */}
            {/* <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Query & AI Response</CardTitle>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(JSON.stringify(sessionData.query, null, 2), "query")}
                    >
                        {copiedSection === "query" ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="bg-muted/50 p-4 rounded-lg font-mono text-sm overflow-x-auto text-foreground">
                        <pre>{JSON.stringify(sessionData.query, null, 2)}</pre>
                    </div>
                </CardContent>
            </Card> */}

            {/* Company Insights */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Company Insights</CardTitle>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(JSON.stringify(sessionData.company_insights, null, 2), "insights")}
                    >
                        {copiedSection === "insights" ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="bg-muted/50 p-4 rounded-lg font-mono text-sm overflow-x-auto text-foreground">
                        <pre>{JSON.stringify(sessionData.company_insights, null, 2)}</pre>
                    </div>
                </CardContent>
            </Card>

            {/* Extracted Q&A */}
            {sessionData.extracted_qa.length > 0 && (
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Extracted Q&A ({sessionData.extracted_qa.length})</CardTitle>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(JSON.stringify(sessionData.extracted_qa, null, 2), "qa")}
                        >
                            {copiedSection === "qa" ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        </Button>
                    </CardHeader>
                    <CardContent>
                        <div className="bg-muted/50 p-4 rounded-lg font-mono text-sm overflow-x-auto text-foreground">
                            <pre>{JSON.stringify(sessionData.extracted_qa, null, 2)}</pre>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Conversation */}
            <Card>
                <CardHeader>
                    <CardTitle>Ask Follow-up Questions</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {/* Conversation History */}
                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <h4 className="font-medium">Conversation History ({conversation.length})</h4>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                        copyToClipboard(JSON.stringify(sessionData.conversation_history, null, 2), "conversation")
                                    }
                                >
                                    {copiedSection === "conversation" ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                </Button>
                            </div>

                            <ScrollArea className="h-64">
                                <div className="space-y-3">
                                    {conversation.map((message) => (
                                        <div key={message.id} className="flex gap-3">
                                            <div
                                                className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${message.type === "user" ? "bg-blue-100 text-blue-600" : "bg-gray-100 text-gray-600"}`}
                                            >
                                                {message.type === "user" ? <User className="w-3 h-3" /> : <Bot className="w-3 h-3" />}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="text-sm font-medium">{message.type === "user" ? "You" : "WebSage AI"}</span>
                                                    <span className="text-xs text-gray-500">{formatDate(message.timestamp)}</span>
                                                </div>
                                                <div className="text-sm bg-muted/50 p-2 rounded border text-foreground">{message.message}</div>
                                            </div>
                                        </div>
                                    ))}
                                    {conversation.length === 0 && (
                                        <div className="text-sm text-gray-500 text-center py-4">
                                            No conversation yet. Ask a question below to start.
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </div>

                        <Separator />

                        {/* Follow-up Question Input */}
                        <div className="flex gap-2">
                            <Input
                                placeholder="What else would you like to know about this website?"
                                value={followUpQuestion}
                                onChange={(e) => setFollowUpQuestion(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleAskFollowUp()}
                            />
                            <Button onClick={handleAskFollowUp} disabled={!followUpQuestion.trim() || isAsking} size="sm">
                                {isAsking ? (
                                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                ) : (
                                    <Send className="w-4 h-4" />
                                )}
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
