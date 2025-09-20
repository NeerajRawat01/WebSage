export async function GET(req: Request, { params }: any) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const secret = process.env.API_SECRET_KEY;
  if (!secret) {
    return new Response(
      JSON.stringify({ error: "Server misconfigured: missing API secret" }),
      { status: 500 }
    );
  }
  const res = await fetch(`${backendUrl}/analyze/sessions/${params.id}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${secret}` },
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  return new Response(JSON.stringify(data), { status: res.status });
}
