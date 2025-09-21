export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET(req: Request, { params }: any) {
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const secret = process.env.API_SECRET_KEY;
  if (!secret) {
    return new Response(
      JSON.stringify({ error: "Server misconfigured: missing API secret" }),
      { status: 500 }
    );
  }
  try {
    const res = await fetch(`${backendUrl}/analyze/sessions/${params.id}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${secret}` },
      cache: "no-store",
    });
    const data = await res.json().catch(() => ({}));
    return new Response(JSON.stringify(data), { status: res.status });
  } catch (e: any) {
    const message = e?.message || "Upstream fetch failed";
    return new Response(JSON.stringify({ error: message, backendUrl }), {
      status: 502,
    });
  }
}
