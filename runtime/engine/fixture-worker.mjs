// B01 deterministic transport spike using real pinned Pi Agent/Pi AI modules.
// This capability is explicitly fixture-only; no API/model/provider success claim.
import { Agent } from '@earendil-works/pi-agent-core';
import { createAssistantMessageEventStream } from '@earendil-works/pi-ai/utils/event-stream';
import { readFrames, writeFrame } from './framing.mjs';

const workerId = 'worker-fixture';
const id = value => typeof value === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(value);
let active;
let disconnected = false;
const model = { id: 'deterministic-fixture', name: 'B01 fixture', api: 'openai-completions',
  provider: 'toddy-fixture', baseUrl: '', reasoning: false, input: ['text'],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 }, contextWindow: 4096, maxTokens: 256 };

function response(content, stopReason) {
  return { role: 'assistant', content, api: model.api, provider: model.provider, model: model.id,
    usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0,
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } },
    stopReason, timestamp: Date.now() };
}

async function send(run, kind, body) {
  if (disconnected) throw Error('disconnected');
  await writeFrame(process.stdout, { version: 1, kind, worker_id: workerId,
    run_id: run.run_id, request_id: run.request_id, seq: ++run.outSequence, ...body });
}

function check(message) {
  if (!message || typeof message !== 'object' || Array.isArray(message) ||
      message.version !== 1 || message.worker_id !== workerId ||
      !id(message.run_id) || !id(message.request_id) ||
      !Number.isSafeInteger(message.seq) || message.seq < 1) throw Error('invalid_envelope');
  const common = ['version', 'kind', 'worker_id', 'run_id', 'request_id', 'seq'];
  const extra = { run: ['input', 'profile_revision'], tool_result: ['tool_call_id', 'content'], cancel: [] }[message.kind];
  if (!extra || Object.keys(message).some(k => !common.includes(k) && !extra.includes(k)) ||
      [...common, ...extra].some(k => !Object.hasOwn(message, k))) throw Error('invalid_fields');
  if (message.kind !== 'run' && (!active || message.run_id !== active.run_id ||
      message.request_id !== active.request_id || message.seq <= active.inSequence)) throw Error('out_of_run');
}

async function start(message) {
  if (active || typeof message.input !== 'string' || Buffer.byteLength(message.input) > 16384 ||
      !/^[a-f0-9]{64}$/.test(message.profile_revision)) throw Error('invalid_run');
  const run = { ...message, inSequence: message.seq, outSequence: 0, pending: new Map() };
  active = run;
  let calls = 0;
  const streamFn = (_model, context) => {
    const stream = createAssistantMessageEventStream();
    const first = calls++ === 0;
    if (!first && !context.messages.some(m => m.role === 'toolResult' &&
        m.content.some(c => c.type === 'text' && c.text === 'NAME=Toddy OS fixture'))) throw Error('fixture_result_missing');
    const content = first ? [{ type: 'toolCall', id: 'tool-fixture', name: 'read_fixture', arguments: { name: 'os-release' } }] :
      [{ type: 'text', text: 'Verified fixture tool result.' }];
    const answer = response(content, first ? 'toolUse' : 'stop');
    queueMicrotask(() => {
      stream.push({ type: 'start', partial: answer });
      if (!first) stream.push({ type: 'text_delta', contentIndex: 0, delta: content[0].text, partial: answer });
      stream.push({ type: 'done', reason: answer.stopReason, message: answer });
    });
    return stream;
  };
  const agent = new Agent({ initialState: { model, systemPrompt: 'B01 deterministic fixture only.',
    tools: [{ name: 'read_fixture', label: 'Read fixture', description: 'Read fictional OS metadata.',
      parameters: { type: 'object', properties: { name: { type: 'string', enum: ['os-release'] } }, required: ['name'], additionalProperties: false },
      executionMode: 'sequential', replay: 'never',
      execute: (toolCallId, args, signal) => new Promise((resolve, reject) => {
        if (signal?.aborted || run.pending.size) return reject(Error('canceled_or_busy'));
        const abort = () => { run.pending.delete(toolCallId); reject(Error('canceled')); };
        signal?.addEventListener('abort', abort, { once: true });
        run.pending.set(toolCallId, { resolve: result => {
          signal?.removeEventListener('abort', abort); resolve(result);
        }, reject });
        send(run, 'tool_request', { tool_call_id: toolCallId, tool: 'read_fixture', arguments: args }).catch(reject);
      }) }] }, streamFn, toolExecution: 'sequential', maxRetryDelayMs: 0 });
  run.agent = agent;
  agent.subscribe(event => {
    if (event.type === 'message_update' && event.assistantMessageEvent.type === 'text_delta')
      return send(run, 'text', { text: event.assistantMessageEvent.delta });
  });
  run.promise = agent.prompt(message.input).then(async () => {
    const canceled = run.cancelRequested || agent.state.messages.some(m => m.role === 'assistant' && m.stopReason === 'aborted');
    if (!disconnected) await send(run, 'done', { state: canceled ? 'canceled' : agent.errorMessage ? 'failed' : 'completed' });
  }).catch(async () => {
    if (!disconnected) await send(run, 'error', { code: 'fixture_run_failed' });
  }).finally(() => { active = undefined; });
}

process.stdout.on('error', () => { disconnected = true; active?.agent.abort(); });
try {
  await writeFrame(process.stdout, { version: 1, kind: 'hello', worker_id: workerId,
    capabilities: ['fixture-tool', 'cancel'], max_frame: 1048576 });
  for await (const message of readFrames(process.stdin)) {
    check(message);
    if (message.kind === 'run') await start(message);
    else {
      active.inSequence = message.seq;
      if (message.kind === 'cancel') { active.cancelRequested = true; active.agent.abort(); }
      else {
        if (typeof message.content !== 'string' || Buffer.byteLength(message.content) > 262144 ||
            !active.pending.has(message.tool_call_id)) throw Error('invalid_tool_result');
        const pending = active.pending.get(message.tool_call_id);
        active.pending.delete(message.tool_call_id);
        pending.resolve({ content: [{ type: 'text', text: message.content }], details: { fixture: true } });
      }
    }
  }
  if (active) { disconnected = true; active.agent.abort(); await active.promise; }
} catch {
  disconnected = true;
  active?.agent.abort();
  process.stderr.write('worker_protocol_error\n');
  process.exitCode = 2;
}
