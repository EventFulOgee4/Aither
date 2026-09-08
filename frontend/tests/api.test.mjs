import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { ensureFreshAccessToken } from '../src/api/client.js';
import { getMessages, sendMessageStream } from '../src/api/chat.js';

const token = `header.${btoa(JSON.stringify({ exp: Date.now() / 1000 + 3600 }))}.signature`;
beforeEach(() => {
  const storage = new Map([['access', token], ['refresh', 'refresh-token']]);
  globalThis.localStorage = {
    getItem: (key) => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value),
    removeItem: (key) => storage.delete(key),
  };
});

test('loads all message pages in order', async () => {
  globalThis.fetch = async (url) => {
    const page = Number(new URL(url).searchParams.get('page'));
    return Response.json({ next: page === 1 ? '?page=2' : null, results: [{ id: page, sender: 'user', message: `Page ${page}` }] });
  };
  assert.deepEqual((await getMessages(1)).map((m) => m.content), ['Page 1', 'Page 2']);
});

test('shares a token refresh across concurrent callers', async () => {
  localStorage.setItem('access', 'expired');
  let requests = 0;
  globalThis.fetch = async () => { requests++; return Response.json({ access: token, refresh: 'rotated' }); };
  assert.deepEqual(await Promise.all([ensureFreshAccessToken(), ensureFreshAccessToken()]), [token, token]);
  assert.equal(requests, 1);
  assert.equal(localStorage.getItem('refresh'), 'rotated');
});

test('temporary network failure preserves refresh credentials', async () => {
  localStorage.setItem('access', 'expired');
  globalThis.fetch = async () => { throw new TypeError('offline'); };
  await assert.rejects(ensureFreshAccessToken());
  assert.equal(localStorage.getItem('refresh'), 'refresh-token');
});

test('stream handles fragmented UTF-8 and terminal metadata', async () => {
  const bytes = new TextEncoder().encode('data: {"type":"chunk","text":"Hi 🙂"}\n\ndata: {"type":"done","ai_message_id":4}\n\n');
  globalThis.fetch = async () => new Response(new ReadableStream({ start(controller) {
    for (const byte of bytes) controller.enqueue(Uint8Array.of(byte));
    controller.close();
  } }));
  let output = '';
  const done = await new Promise((resolve, reject) => sendMessageStream('Hi', 1, { onChunk: (text) => { output += text; }, onDone: resolve, onError: reject }));
  assert.equal(output, 'Hi 🙂');
  assert.equal(done.ai_message_id, 4);
});

test('truncated stream reports failure instead of staying busy', async () => {
  globalThis.fetch = async () => new Response('data: {"type":"chunk","text":"partial"}\n\n');
  const error = await new Promise((resolve) => sendMessageStream('Hi', 1, { onError: resolve }));
  assert.match(error.message, /interrupted/);
});

test('server error event reaches the caller', async () => {
  globalThis.fetch = async () => new Response('data: {"type":"error","message":"Please retry"}\n\n');
  const error = await new Promise((resolve) => sendMessageStream('Hi', 1, { onError: resolve }));
  assert.equal(error.message, 'Please retry');
});
