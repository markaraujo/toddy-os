import assert from 'node:assert/strict';
import { test } from 'node:test';
import { PassThrough } from 'node:stream';
import { createAssistantMessageEventStream } from '@earendil-works/pi-ai/utils/event-stream';
import { serveWorker, validateBootstrap } from './worker.mjs';
import { writeFrame, readFrames } from './framing.mjs';

const model = { id: 'synthetic-protocol-only', name: 'Synthetic', api: 'openai-completions',
  provider: 'toddy-test', baseUrl: '', reasoning: false, input: ['text'],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 4096, maxTokens: 128 };
const answer = (content, stopReason) => ({ role: 'assistant', content, api: model.api, provider: model.provider,
  model: model.id, usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } }, stopReason, timestamp: Date.now() });
const bootstrap = () => ({ version: 1, profile_revision: 'a'.repeat(64),
  profile: { schema_version: 1, budgets: { task_deadline_seconds: 5, max_tool_calls: 2 } },
  connection: { credential: 'dummy-secret-not-model-context' }, catalog: {}, system_prompt: 'Protocol test only.',
  remote_consent: false, tools: [{ name: 'read-file', label: 'Read file', description: 'Broker owned harmless tool',
    parameters: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'], additionalProperties: false } }] });

function factory({ tool = true, endless = false, fail } = {}) {
  let turns = 0;
  return async (_profile, _connection, _catalog) => ({ model, streamFn(_model, context) {
    assert.ok(!JSON.stringify(context).includes('dummy-secret-not-model-context'));
    const stream = createAssistantMessageEventStream();
    const first = turns++ === 0;
    const calls = tool && (first || endless);
    const content = calls ? [{ type: 'toolCall', id: 'upstream-tool-' + turns,
      name: 'read-file', arguments: { path: 'fixture.txt' } }] : [{ type: 'text', text: 'Actual broker result: harmless.' }];
    const result = answer(content, calls ? 'toolUse' : 'stop');
    queueMicrotask(() => {
      if (fail) {
        stream.push({ type: 'error', reason: 'error', error: { ...result, stopReason: 'error', errorMessage: fail } });
      } else {
        stream.push({ type: 'start', partial: result });
        if (!calls) stream.push({ type: 'text_delta', contentIndex: 0, delta: content[0].text, partial: result });
        stream.push({ type: 'done', reason: result.stopReason, message: result });
      }
    });
    return stream;
  } });
}

async function harness(options = {}, boot = bootstrap()) {
  const input = new PassThrough();
  const output = new PassThrough();
  const finished = serveWorker({ input, output, bootstrap: boot, providerFactory: factory(options) });
  const events = readFrames(output)[Symbol.asyncIterator]();
  const hello = (await events.next()).value;
  assert.deepEqual(hello.capabilities, ['agent-runtime-v1', 'runtime-tool-result-v1', 'single-run', 'cancel']);
  const base = { version: 1, worker_id: hello.worker_id, run_id: 'run-one', request_id: 'request-one' };
  return { input, output, finished, events, base,
    run: () => writeFrame(input, { ...base, kind: 'run', seq: 1, input: 'Use the declared tool.', profile_revision: boot.profile_revision }),
    close: async () => { input.end(); const code = await finished; output.end(); return code; } };
}

function bounded(promise, ms = 3000) {
  return Promise.race([promise, new Promise((_, reject) => {
    const timeout = setTimeout(() => reject(Error('test_deadline')), ms);
    promise.finally(() => clearTimeout(timeout));
  })]);
}

test('real Pi loop delegates tool then streams text; private connection never model context', async () => {
  const h = await harness(); await h.run();
  const request = (await h.events.next()).value;
  assert.equal(request.kind, 'tool_request'); assert.equal(request.tool, 'read-file');
  assert.equal(request.seq, 1); assert.equal(request.tool_call_id, 'tool-1');
  await writeFrame(h.input, { ...h.base, kind: 'tool_result', seq: 2,
    tool_call_id: request.tool_call_id, content: 'harmless', outcome: 'verified' });
  const text = (await h.events.next()).value;
  assert.equal(text.kind, 'text'); assert.equal(text.seq, 2);
  const done = (await h.events.next()).value;
  assert.equal(done.state, 'completed'); assert.equal(done.seq, 3);
  assert.equal(await h.close(), 0);
});

test('uncertain effect aborts further tools and never emits completed', async () => {
  const h = await harness({ endless: true }); await h.run();
  const request = (await h.events.next()).value;
  await writeFrame(h.input, { ...h.base, kind: 'tool_result', seq: 2,
    tool_call_id: request.tool_call_id, content: 'review required', outcome: 'uncertain' });
  const done = await bounded(h.events.next());
  assert.equal(done.value.kind, 'done'); assert.equal(done.value.state, 'failed');
  assert.equal(done.value.code, 'tool_outcome_uncertain');
  assert.equal(await h.close(), 0);
});

test('Stop aborts a pending tool independently of model behavior', async () => {
  const h = await harness(); await h.run(); await h.events.next();
  await writeFrame(h.input, { ...h.base, kind: 'cancel', seq: 2 });
  const done = await bounded(h.events.next());
  assert.equal(done.value.state, 'canceled'); assert.equal(done.value.code, 'canceled');
  assert.equal(await h.close(), 0);
});

test('tool budget is enforced before emitting an extra request', async () => {
  const h = await harness({ endless: true }, { ...bootstrap(), profile: { schema_version: 1,
    budgets: { task_deadline_seconds: 5, max_tool_calls: 1 } } });
  await h.run(); const request = (await h.events.next()).value;
  await writeFrame(h.input, { ...h.base, kind: 'tool_result', seq: 2,
    tool_call_id: request.tool_call_id, content: 'harmless', outcome: 'verified' });
  const done = await bounded(h.events.next());
  assert.equal(done.value.kind, 'done'); assert.equal(done.value.state, 'failed');
  assert.equal(done.value.code, 'tool_dispatch_blocked');
  assert.equal(await h.close(), 0);
});

test('deadline and disconnect both release an unresolved tool promise', async () => {
  const boot = bootstrap(); boot.profile.budgets.task_deadline_seconds = 1;
  const h = await harness({}, boot); await h.run(); await h.events.next();
  const done = await bounded(h.events.next());
  assert.equal(done.value.state, 'canceled'); assert.equal(done.value.code, 'task_deadline');
  assert.equal(await h.close(), 0);
  const disconnected = await harness(); await disconnected.run(); await disconnected.events.next();
  assert.equal(await bounded(disconnected.close()), 0);
});

test('wrong result IDs, stale sequences and foreign profile revisions reject dispatch', async () => {
  for (const change of [message => ({ ...message, tool_call_id: 'wrong' }), message => ({ ...message, seq: 1 })]) {
    const h = await harness(); await h.run(); const request = (await h.events.next()).value;
    await writeFrame(h.input, change({ ...h.base, kind: 'tool_result', seq: 2,
      tool_call_id: request.tool_call_id, content: 'not used', outcome: 'verified' }));
    assert.equal(await bounded(h.finished), 2); h.input.end(); h.output.end();
  }
  const h = await harness();
  await writeFrame(h.input, { ...h.base, kind: 'run', seq: 1, input: 'No effect.', profile_revision: 'b'.repeat(64) });
  assert.equal(await bounded(h.finished), 2); h.input.end(); h.output.end();
});

test('raw provider errors are replaced by fixed classified codes', async () => {
  const h = await harness({ tool: false, fail: 'dummy-secret-raw-error' }); await h.run();
  const done = (await h.events.next()).value;
  assert.equal(done.state, 'failed'); assert.equal(done.code, 'provider_failed');
  assert.ok(!JSON.stringify(done).includes('dummy-secret'));
  assert.equal(await h.close(), 0);
});

test('bootstrap rejects unknown fields, duplicate tools, unsafe revisions and oversized persona', () => {
  assert.throws(() => validateBootstrap({ ...bootstrap(), root_grant: true }));
  const duplicate = bootstrap(); duplicate.tools.push(duplicate.tools[0]);
  assert.throws(() => validateBootstrap(duplicate));
  assert.throws(() => validateBootstrap({ ...bootstrap(), profile_revision: '../escape' }));
  assert.throws(() => validateBootstrap({ ...bootstrap(), system_prompt: 'x'.repeat(32769) }));
});
