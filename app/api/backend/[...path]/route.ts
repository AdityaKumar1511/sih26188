import { NextRequest, NextResponse } from 'next/server';

export const maxDuration = 60;
export const dynamic = 'force-dynamic';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://sih-sentinel-backend.onrender.com';

async function handleProxy(req: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? params.path.join('/') : '';
  const search = req.nextUrl.search || '';
  const base = BACKEND_URL.replace(/\/+$/, '');
  const targetUrl = base + '/' + path + search;

  try {
    const headers = new Headers();
    const contentType = req.headers.get('content-type');
    if (contentType) {
      headers.set('content-type', contentType);
    }
    const accept = req.headers.get('accept');
    if (accept) {
      headers.set('accept', accept);
    }

    const body = req.method !== 'GET' && req.method !== 'HEAD' ? await req.arrayBuffer() : undefined;

    const response = await fetch(targetUrl, {
      method: req.method,
      headers: headers,
      body: body,
      cache: 'no-store',
    });

    const respHeaders = new Headers(response.headers);
    respHeaders.set('Access-Control-Allow-Origin', '*');
    respHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    respHeaders.set('Access-Control-Allow-Headers', '*');

    const respBody = await response.arrayBuffer();
    return new NextResponse(respBody, {
      status: response.status,
      headers: respHeaders,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Backend proxy error', details: err?.message || String(err) },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest, ctx: any) {
  return handleProxy(req, ctx);
}

export async function POST(req: NextRequest, ctx: any) {
  return handleProxy(req, ctx);
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    },
  });
}
