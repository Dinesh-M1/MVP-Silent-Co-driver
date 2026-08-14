import { NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.BACKEND_URL ||
  'http://127.0.0.1:8001/api/v1/analyze';

const TIMEOUT_MS = 15000;

export async function POST(request: Request) {
  let timeoutId: ReturnType<typeof setTimeout> | undefined;

  try {
    const body = await request.json();
    const controller = new AbortController();

    timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    const backendResponse = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
      cache: 'no-store',
    });

    const responseText = await backendResponse.text();

    if (!backendResponse.ok) {
      return NextResponse.json(
        {
          detail: `Backend Error (${backendResponse.status})`,
          backend_response: responseText,
        },
        { status: backendResponse.status },
      );
    }

    let data: unknown;

    try {
      data = JSON.parse(responseText);
    } catch {
      return NextResponse.json(
        {
          detail: 'Backend returned invalid JSON.',
          backend_response: responseText,
        },
        { status: 502 },
      );
    }

    return NextResponse.json(data);
  } catch (error: unknown) {
    if (
      error instanceof Error &&
      error.name === 'AbortError'
    ) {
      return NextResponse.json(
        { detail: 'Backend request timed out after 15 seconds.' },
        { status: 504 },
      );
    }

    return NextResponse.json(
      {
        detail:
          error instanceof Error
            ? error.message
            : 'Failed to connect to backend service.',
      },
      { status: 502 },
    );
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
  }
}
