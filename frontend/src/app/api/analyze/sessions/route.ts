export async function GET() {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const secret = process.env.API_SECRET_KEY;
  if (!secret) {
    return new Response(JSON.stringify([]), { status: 200 });
  }
  const res = await fetch(`${backendUrl}/analyze/sessions`, {
    method: "GET",
    headers: { Authorization: `Bearer ${secret}` },
    cache: "no-store",
  });
  const data = await res.json().catch(() => []);
  return new Response(JSON.stringify(data), { status: res.status });
}
