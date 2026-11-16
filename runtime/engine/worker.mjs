// Production Pi1.5 worker. Connections/credentials arrive only on a private FD;
// the worker owns no canonical task store, root policy or native tool effects.
import { closeSync, fstatSync, readSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { setImmediate as yieldTurn } from 'node:timers/promises';
import { Agent } from '@earendil-works/pi-agent-core';
import { createProvider } from './provider.mjs';
import { MAX_FRAME, strictJSON, readFrames, writeFrame } from './framing.mjs';

const WORKER = 'worker-runtime';
const id = value => typeof value === 'string' && /^[a-z][a-z0-9-]{0,63}$/.test(value);
const exact = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const bytes = value => Buffer.byteLength(value, 'utf8');
const providerCodes = new Set(['provider_auth_denied', 'provider_rate_limited', 'provider_unavailable',
  'provider_failed', 'provider_context_limit', 'provider_tool_limit', 'provider_output_limit',
  'provider_deadline', 'provider_input_limit', 'provider_response_limit', 'provider_retry_blocked',
  'provider_origin_blocked', 'provider_request_limit', 'provider_busy', 'provider_incomplete',
  'backend_deferred', 'remote_consent_required', 'credential_unavailable', 'adapter_unavailable',
  'model_unavailable', 'invalid_provider_config', 'invalid_provider_budget', 'invalid_provider_endpoint',
  'local_preflight_failed', 'local_preflight_limit', 'local_template_unsupported', 'local_connection_mismatch',
  'remote_fallback_blocked']);
const safeCode = value => providerCodes.has(value) ? value : 'provider_failed';

export function validateBootstrap(bootstrap) {
  if (!exact(bootstrap, ['version', 'profile_revision', 'profile', 'connection', 'catalog', 'system_prompt', 'tools', 'remote_consent']) ||
      bootstrap.version !== 1 || !/^[a-f0-9]{64}$/.test(bootstrap.profile_revision) ||
      !bootstrap.profile || bootstrap.profile.schema_version !== 1 ||
      typeof bootstrap.system_prompt !== 'string' || bytes(bootstrap.system_prompt) > 32768 ||
      typeof bootstrap.remote_consent !== 'boolean' || !Array.isArray(bootstrap.tools) || bootstrap.tools.length > 32 ||
      !bootstrap.catalog || typeof bootstrap.catalog !== 'object' || Array.isArray(bootstrap.catalog)) throw Error('invalid_bootstrap');
  const budget = bootstrap.profile.budgets;
  if (!budget || !Number.isSafeInteger(budget.task_deadline_seconds) || budget.task_deadline_seconds < 1 || budget.task_deadline_seconds > 3600 ||
      !Number.isSafeInteger(budget.max_tool_calls) || budget.max_tool_calls < 0 || budget.max_tool_calls > 32) throw Error('invalid_bootstrap');
  const names = new Set();
  for (const tool of bootstrap.tools) {
    if (!exact(tool, ['name', 'label', 'description', 'parameters']) || !id(tool.name) || names.has(tool.name) ||
        typeof tool.label !== 'string' || bytes(tool.label) > 128 || typeof tool.description !== 'string' || bytes(tool.description) > 4096 ||
        !tool.parameters || typeof tool.parameters !== 'object' || Array.isArray(tool.parameters) ||
        bytes(JSON.stringify(tool.parameters)) > 32768) throw Error('invalid_tool_definition');
    names.add(tool.name);
  }
  return bootstrap;
}

export function readBootstrap(descriptor) {
  if (process.getuid() === 0 || !Number.isSafeInteger(descriptor) || descriptor < 3) throw Error('private_bootstrap_missing');
  try {
    const info = fstatSync(descriptor);
    if (!info.isFile() || info.uid !== process.getuid() || (info.mode & 0o077) || info.size > 65536) throw Error('private_bootstrap_invalid');
    const buffer = Buffer.alloc(65537);
    const count = readSync(descriptor, buffer, 0, buffer.length, 0);
    if (!count || count > 65536 || count !== info.size) throw Error('private_bootstrap_limit');
    return validateBootstrap(strictJSON(new TextDecoder('utf-8', { fatal: true }).decode(buffer.subarray(0, count))));
  } finally { closeSync(descriptor); }
}

// providerFactory injection is for module-level tests only. The CLI below never
// accepts an override/env module and always uses the production createProvider.
export async function serveWorker({ input = process.stdin, output = process.stdout, bootstrap,
  providerFactory = createProvider } = {}) {
  validateBootstrap(bootstrap);
  let active;
  let used = false;
  let disconnected = false;
  let writes = 0;
  let tail = Promise.resolve();
  let protocolFailed = false;

  function send(message) {
    if (disconnected || writes >= 32) throw Error('worker_output_unavailable');
    writes++;
    const write = tail.then(async () => {
      let timeout;
      try {
        await Promise.race([writeFrame(output, message), new Promise((_, reject) => {
          timeout = setTimeout(() => reject(Error('worker_output_deadline')), 5000);
        })]);
      } finally { clearTimeout(timeout); }
    });
    tail = write.catch(() => { disconnected = true; abortActive('worker_disconnected'); });
    return write.finally(() => { writes--; });
  }
  const envelope = (run, kind, body) => ({ version: 1, kind, worker_id: WORKER,
    run_id: run.run_id, request_id: run.request_id, seq: ++run.outSequence, ...body });
  const event = (run, kind, body) => send(envelope(run, kind, body));

  function abortActive(code) {
    if (!active) return;
    active.cancelRequested = true;
    active.failureCode = active.failureCode ?? code;
    active.agent?.abort();
    for (const pending of active.pending.values()) pending.reject(Error('canceled'));
    active.pending.clear();
  }

  output.on('error', () => { disconnected = true; abortActive('worker_disconnected'); });
  function check(message) {
    const common = ['version', 'kind', 'worker_id', 'run_id', 'request_id', 'seq'];
    const extras = { run: ['input', 'profile_revision'], cancel: [],
      tool_result: ['tool_call_id', 'content', 'outcome'] }[message?.kind];
    if (!extras || !exact(message, [...common, ...extras]) || message.version !== 1 || message.worker_id !== WORKER ||
        !id(message.run_id) || !id(message.request_id) || !Number.isSafeInteger(message.seq) || message.seq < 1) throw Error('invalid_envelope');
    if (message.kind !== 'run' && (!active || message.run_id !== active.run_id || message.request_id !== active.request_id ||
        message.seq <= active.inSequence)) throw Error('out_of_run');
  }

  function start(message) {
    if (used || active || typeof message.input !== 'string' || !bytes(message.input) || bytes(message.input) > 16384 ||
        message.profile_revision !== bootstrap.profile_revision) throw Error('invalid_run');
    used = true;
    const run = { ...message, inSequence: message.seq, outSequence: 0, pending: new Map(), calls: 0, textBytes: 0,
      cancelRequested: false, failureCode: undefined };
    active = run;
    const deadline = setTimeout(() => abortActive('task_deadline'), bootstrap.profile.budgets.task_deadline_seconds * 1000);
    run.promise = (async () => {
      try {
        const provider = await providerFactory(bootstrap.profile, bootstrap.connection, bootstrap.catalog,
          { remoteConsent: bootstrap.remote_consent });
        if (run.cancelRequested) return;
        const tools = bootstrap.tools.map(definition => ({ ...definition, executionMode: 'sequential', replay: 'never',
          execute: async (_providerCallId, arguments_, signal) => {
            if (run.cancelRequested || signal?.aborted || run.pending.size ||
                ++run.calls > bootstrap.profile.budgets.max_tool_calls || bytes(JSON.stringify(arguments_)) > 65536) {
              abortActive('tool_dispatch_blocked'); throw Error('tool_dispatch_blocked');
            }
            const toolCallId = 'tool-' + run.calls;
            return new Promise((resolveResult, rejectResult) => {
              const cleanup = () => signal?.removeEventListener('abort', onAbort);
              const onAbort = () => { run.pending.delete(toolCallId); cleanup(); rejectResult(Error('canceled')); };
              signal?.addEventListener('abort', onAbort, { once: true });
              run.pending.set(toolCallId, {
                resolve: result => { cleanup(); resolveResult(result); },
                reject: error => { cleanup(); rejectResult(error); },
              });
              event(run, 'tool_request', { tool_call_id: toolCallId, tool: definition.name, arguments: arguments_ })
                .catch(() => { onAbort(); abortActive('worker_disconnected'); });
            });
          } }));
        const agent = new Agent({ streamFn: provider.streamFn, initialState: { model: provider.model,
          systemPrompt: bootstrap.system_prompt, tools }, toolExecution: 'sequential', maxRetryDelayMs: 0,
          finishTurn: (_turn, signal) => run.cancelRequested || signal?.aborted ? { action: 'end' } : undefined,
          prepareRequest: async () => {
            // Yield even for a malicious/synchronous provider: timers/Stop must
            // not starve behind an infinite chain of resolved tool turns.
            await yieldTurn();
            if (run.cancelRequested) throw Error('canceled');
            run.requests = (run.requests ?? 0) + 1;
            if (run.requests > bootstrap.profile.budgets.max_tool_calls + 1) {
              run.failureCode = 'provider_request_limit'; throw Error('provider_request_limit');
            }
          } });
        run.agent = agent;
        agent.subscribe(async update => {
          if (update.type === 'message_update' && update.assistantMessageEvent?.type === 'text_delta') {
            const text = update.assistantMessageEvent.delta;
            if (typeof text !== 'string' || (run.textBytes += bytes(text)) > 262144) {
              abortActive('worker_text_limit'); throw Error('worker_text_limit');
            }
            await event(run, 'text', { text });
          }
        });
        if (run.cancelRequested) agent.abort();
        else await agent.prompt(message.input);
        const final = agent.state.messages.findLast(item => item.role === 'assistant');
        if (!run.cancelRequested && final?.stopReason !== 'stop') run.failureCode = safeCode(final?.errorMessage);
      } catch (error) {
        run.failureCode = run.failureCode ?? safeCode(error?.code);
      } finally {
        clearTimeout(deadline);
        for (const pending of run.pending.values()) pending.reject(Error('run_finished'));
        run.pending.clear();
        if (!disconnected) {
          const canceled = run.cancelRequested && ['canceled', 'task_deadline'].includes(run.failureCode);
          const state = canceled ? 'canceled' : run.failureCode ? 'failed' : 'completed';
          await event(run, 'done', { state, code: run.failureCode ?? 'completed' }).catch(() => {});
        }
        active = undefined;
      }
    })();
  }

  try {
    await send({ version: 1, kind: 'hello', worker_id: WORKER,
      capabilities: ['agent-runtime-v1', 'runtime-tool-result-v1', 'single-run', 'cancel'], max_frame: MAX_FRAME });
    for await (const message of readFrames(input)) {
      check(message);
      if (message.kind === 'run') start(message);
      else {
        const run = active;
        run.inSequence = message.seq;
        if (message.kind === 'cancel') abortActive('canceled');
        else {
          if (!id(message.tool_call_id) || typeof message.content !== 'string' || bytes(message.content) > 262144 ||
              !['verified', 'rejected', 'uncertain'].includes(message.outcome) || !run.pending.has(message.tool_call_id)) throw Error('invalid_tool_result');
          const pending = run.pending.get(message.tool_call_id);
          run.pending.delete(message.tool_call_id);
          if (message.outcome === 'uncertain') {
            pending.reject(Error('tool_outcome_uncertain'));
            abortActive('tool_outcome_uncertain');
          } else pending.resolve({ content: [{ type: 'text', text: message.content }],
            isError: message.outcome === 'rejected', details: { outcome: message.outcome } });
        }
      }
    }
  } catch {
    protocolFailed = true;
  } finally {
    disconnected = true;
    abortActive('worker_disconnected');
    if (active) await active.promise;
    await tail;
  }
  return protocolFailed ? 2 : 0;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  try {
    const bootstrap = readBootstrap(Number(process.env.TODDY_BOOTSTRAP_FD));
    process.exitCode = await serveWorker({ bootstrap });
  } catch {
    process.stderr.write('worker_bootstrap_invalid\n');
    process.exitCode = 2;
  }
}
