// HTTP semantics over an owned private Unix socket; never DNS/TCP or redirects.
import http from 'node:http';
import { lstat } from 'node:fs/promises';
import { Readable } from 'node:stream';

export async function unixFetch(socketPath) {
  const socket = await lstat(socketPath);
  if (!socket.isSocket() || socket.uid !== process.getuid()) throw Error('local_socket_unavailable');
  return async (input, init) => {
    const request = new Request(input, init);
    const url = new URL(request.url);
    if (url.origin !== 'http://toddy.local' || url.search || url.hash ||
        !['/v1/chat/completions', '/apply-template', '/tokenize'].includes(url.pathname) || request.method !== 'POST') {
      throw Error('local_request_blocked');
    }
    const bytes = new Uint8Array(await request.arrayBuffer());
    if (bytes.length > 1048576) throw Error('local_request_limit');
    return new Promise((resolve, reject) => {
      const outgoing = http.request({ socketPath, path: url.pathname, method: request.method,
        headers: Object.fromEntries(request.headers), signal: request.signal }, incoming => {
        const headers = new Headers();
        for (const [key, value] of Object.entries(incoming.headers)) {
          if (value !== undefined) headers.set(key, Array.isArray(value) ? value.join(', ') : value);
        }
        resolve(new Response(Readable.toWeb(incoming), { status: incoming.statusCode,
          statusText: incoming.statusMessage, headers }));
      });
      outgoing.on('error', reject);
      outgoing.end(bytes);
    });
  };
}
