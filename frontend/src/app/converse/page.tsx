"use client";

import { useEffect, useState } from "react";

type ConverseResponse = {
    url: string;
    user_query: string;
    agent_response: string;
    context_sources: string[];
};

export default function ConversePage() {
    const [url, setUrl] = useState("");
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ConverseResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [sessions, setSessions] = useState<Array<{ id: string; url: string }>>([]);

    // Load recent sessions on mount
    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const res = await fetch("/api/analyze/sessions", { method: "GET" });
                if (!res.ok) return;
                const data = await res.json();
                if (!cancelled) setSessions(data.map((s: any) => ({ id: s.id, url: s.url })));
            } catch { }
        })();
        return () => {
            cancelled = true;
        };
    }, []);

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const res = await fetch("/api/converse", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, query }),
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data?.detail || data?.error || "Request failed");
            }
            setResult(data);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Unexpected error";
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen p-8 flex flex-col items-center gap-8">
            <h1 className="text-2xl font-semibold">WebSage – Converse</h1>
            <form onSubmit={onSubmit} className="flex flex-col gap-3 w-full max-w-xl">
                <select
                    className="border rounded px-3 py-2"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                >
                    <option value="">Select a previously analyzed URL</option>
                    {sessions.map((s) => (
                        <option key={s.id} value={s.url}>{s.url}</option>
                    ))}
                </select>
                <input
                    className="border rounded px-3 py-2"
                    type="text"
                    placeholder="Ask a question about the site"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    required
                />
                <button
                    type="submit"
                    className="border rounded px-4 py-2 bg-black text-white disabled:opacity-50 self-start"
                    disabled={loading}
                >
                    {loading ? "Asking..." : "Ask"}
                </button>
            </form>

            {error && <div className="text-red-600">{error}</div>}

            {result && (
                <pre className="w-full max-w-2xl overflow-auto border rounded p-4 text-white bg-black text-sm">
                    {JSON.stringify(result, null, 2)}
                </pre>
            )}
        </div>
    );
}


