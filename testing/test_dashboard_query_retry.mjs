import assert from 'node:assert/strict';
import test from 'node:test';
import { isTransientReadError, queryClient } from '../frontend/src/lib/query-client.ts';
import { api } from '../frontend/src/lib/api.ts';

test('read query recovers after a temporary service failure', async () => {
  queryClient.setDefaultOptions({ queries: { ...queryClient.getDefaultOptions().queries, retryDelay: 0 } });
  let calls = 0;
  try {
    const value = await queryClient.query({
      queryKey: ['transient-read'],
      queryFn: async () => {
        if (++calls === 1) throw Object.assign(new Error('Service unavailable'), { status: 503 });
        return 'ready';
      },
    });
    assert.equal(value, 'ready');
    assert.equal(calls, 2);
  } finally {
    queryClient.clear();
  }
});

for (const status of [401, 403, 404, 422, 500]) {
  test(`read status ${status} is not retried`, async () => {
    let calls = 0;
    const error = Object.assign(new Error('Rejected'), { status });
    try {
      await assert.rejects(queryClient.query({
        queryKey: ['rejected', status],
        queryFn: async () => { calls++; throw error; },
      }));
      assert.equal(calls, 1);
      assert.equal(isTransientReadError(error), false);
    } finally { queryClient.clear(); }
  });
}

test('ordinary read retries remain bounded', async () => {
  let calls = 0;
  try {
    await assert.rejects(queryClient.query({
      queryKey: ['unavailable-read'],
      queryFn: async () => { calls++; throw Object.assign(new Error('Unavailable'), { status: 503 }); },
    }));
    assert.equal(calls, 3);
  } finally { queryClient.clear(); }
});

test('session bootstrap can recover after several temporary failures', async () => {
  let calls = 0;
  try {
    const value = await queryClient.query({
      queryKey: ['session-bootstrap'],
      retry: (_failures, error) => isTransientReadError(error),
      queryFn: async () => {
        if (++calls < 5) throw Object.assign(new Error('Unavailable'), { status: 503 });
        return 'verified session';
      },
    });
    assert.equal(value, 'verified session');
    assert.equal(calls, 5);
  } finally { queryClient.clear(); }
});

test('writes are sent once even if the service is unavailable', async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response('{"detail":"Unavailable"}', { status: 503 });
  };
  try {
    await assert.rejects(api('/evaluations', { method: 'POST', body: '{}' }), { status: 503 });
    assert.equal(calls, 1);
  } finally { globalThis.fetch = originalFetch; }
});

test('an expired session dispatches logout instead of being retried', async () => {
  const originalFetch = globalThis.fetch;
  const originalWindow = globalThis.window;
  const events = new EventTarget();
  globalThis.window = events;
  let expired = 0;
  events.addEventListener('auth-expired', () => expired++);
  globalThis.fetch = async () => new Response('{"detail":"Sign in"}', { status: 401 });
  try {
    await assert.rejects(api('/me'), { status: 401 });
    assert.equal(expired, 1);
  } finally {
    globalThis.fetch = originalFetch;
    if (originalWindow === undefined) delete globalThis.window;
    else globalThis.window = originalWindow;
  }
});

test('clearing the private cache cancels a pending session check', async () => {
  let started;
  const active = new Promise(resolve => { started = resolve; });
  let aborted = false;
  const pending = queryClient.query({
    queryKey: ['admin', 'pending-session'],
    retry: (_failures, error) => isTransientReadError(error),
    queryFn: ({ signal }) => new Promise((_resolve, reject) => {
      signal.addEventListener('abort', () => { aborted = true; reject(signal.reason); }, { once: true });
      started();
    }),
  });
  const rejected = assert.rejects(pending);
  await active;
  queryClient.clear();
  await rejected;
  assert.equal(aborted, true);
  assert.equal(queryClient.getQueryData(['admin', 'pending-session']), undefined);
});

test('a timed-out read body retains the timeout reason for automatic recovery', async () => {
  const originalFetch = globalThis.fetch;
  const originalTimeout = AbortSignal.timeout;
  let timer;
  AbortSignal.timeout = () => {
    const controller = new AbortController();
    timer = setTimeout(() => controller.abort(new DOMException('Read timed out', 'TimeoutError')), 10);
    return controller.signal;
  };
  globalThis.fetch = async (_url, { signal }) => new Response(new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode('{"username":'));
      signal.addEventListener('abort', () => controller.error(signal.reason), { once: true });
    },
  }), { status: 200 });
  try {
    await assert.rejects(api('/me'), { name: 'TimeoutError' });
  } finally {
    clearTimeout(timer);
    globalThis.fetch = originalFetch;
    AbortSignal.timeout = originalTimeout;
  }
});
