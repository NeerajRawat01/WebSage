"use client";

import { useState } from "react";

type QAItem = { question: string; answer: string };
type AnalyzeResponse = {
    url: string;
    analysis_timestamp: string;
    company_info: Record<string, unknown>;
    extracted_answers: QAItem[];
};

export default function AnalyzePage() {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<AnalyzeResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const res = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
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
            <h1 className="text-2xl font-semibold">Analyze a Website</h1>
            <form onSubmit={onSubmit} className="flex gap-2 w-full max-w-xl">
                <input
                    className="flex-1 border rounded px-3 py-2"
                    type="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    required
                />
                <button
                    type="submit"
                    className="border rounded px-4 py-2 bg-black text-white disabled:opacity-50"
                    disabled={loading}
                >
                    {loading ? "Analyzing..." : "Analyze"}
                </button>
            </form>

            {error && <div className="text-red-600">{error}</div>}

            {result && (
                <pre className="w-full max-w-2xl overflow-auto border rounded p-4 bg-gray-300 text-sm">
                    {JSON.stringify(result, null, 2)}
                </pre>
            )}
        </div>
    );
}


