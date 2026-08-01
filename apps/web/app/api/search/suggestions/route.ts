import { NextResponse } from "next/server";

import { getSessionToken } from "@/lib/session";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://api:8000";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("q") ?? "";

  if (!query || query.length < 2) {
    return NextResponse.json({ suggestions: [], query });
  }

  try {
    const token = await getSessionToken();
    const upstream = await fetch(
      `${API_BASE_URL}/api/search/suggestions?q=${encodeURIComponent(query)}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
      },
    );

    if (!upstream.ok) {
      return NextResponse.json({ suggestions: [], query });
    }

    const data: unknown = await upstream.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ suggestions: [], query });
  }
}
