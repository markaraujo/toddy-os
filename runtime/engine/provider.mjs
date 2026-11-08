// Pi 1.5.0 adapter boundary. Private connection data never enters the model.
import { createAssistantMessageEventStream } from '@earendil-works/pi-ai/utils/event-stream';
import { unixFetch } from './local-transport.mjs';

const adapters = Object.freeze({
  'local-llama-cpp': { api: 'openai-completions', provider: 'toddy-local' },
  'openai-compatible': { api: 'openai-completions', provider: 'toddy-compatible' },
  openrouter: { api: 'openai-completions', provider: 'openrouter' },
  openai: { api: 'openai-responses', provider: 'openai' },
  anthropic: { api: 'anthropic-messages', provider: 'anthropic' },
});
const keys = (object, expected) => object && typeof object === 'object' && !Array.isArray(object) &&
  Object.keys(object).length === expected.length && expected.every(key => Object.hasOwn(object, key));
const integer = (value, min, max) => Number.isSafeInteger(value) && value >= min && value <= max;
async function boundedJson(response) {
  if (!response.ok || !response.body) {
    const error = new ProviderError('local_preflight_failed');
    error.httpStatus = response.status;
    throw error;
  }
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const item = await reader.read();
      if (item.done) break;
      size += item.value.byteLength;
      if (size > 1048576) throw new ProviderError('local_preflight_limit');
      chunks.push(item.value);
    }
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
  } finally { await reader.cancel().catch(() => {}); }
}
export class ProviderError extends Error {
  constructor(code) { super(code); this.code = code; }
}

export async function createProvider(profile, connection, catalog, { remoteConsent = false, fetchImpl, fixtureObserver } = {}) {
  // This validates the provider/reference subset, not B05 profile activation.
  if (profile?.schema_version !== 1 || !keys(profile.provider,
    ['mode', 'adapter_id', 'model_id', 'connection_ref', 'allow_remote_fallback'])) {
    throw new ProviderError('invalid_provider_config');
  }
  const choice = structuredClone(profile.provider);
  const budget = structuredClone(profile.budgets);
  if (choice.allow_remote_fallback !== false) throw new ProviderError('remote_fallback_blocked');
  if (choice.mode === 'deferred') throw new ProviderError('backend_deferred');
  const adapter = adapters[choice.adapter_id];
  if (!adapter || !['local', 'remote'].includes(choice.mode) ||
      (choice.mode === 'local') !== (choice.adapter_id === 'local-llama-cpp')) {
    throw new ProviderError('adapter_unavailable');
  }
  const record = catalog[choice.model_id];
  if (!record || record.adapter_id !== choice.adapter_id || !record.qualified ||
      !integer(record.context_tokens, 256, 1048576) || !integer(record.max_output_tokens, 1, record.context_tokens)) {
    throw new ProviderError('model_unavailable');
  }
  if (!budget || !integer(budget.max_context_tokens, 256, record.context_tokens) ||
      !integer(budget.max_output_tokens, 1, Math.min(record.max_output_tokens, budget.max_context_tokens)) ||
      !integer(budget.task_deadline_seconds, 1, 3600) || !integer(budget.max_tool_calls, 0, 32) ||
      budget.max_retries !== 0 || typeof budget.remote_spending_enabled !== 'boolean') {
    throw new ProviderError('invalid_provider_budget');
  }
  if (choice.mode === 'remote' && (!remoteConsent || !budget.remote_spending_enabled)) {
    throw new ProviderError('remote_consent_required');
  }
  if (!connection || connection.id !== choice.connection_ref ||
      typeof connection.credential !== 'string' || !/^[\x21-\x7e]{1,4096}$/.test(connection.credential)) {
    throw new ProviderError('credential_unavailable');
  }
  const credential = connection.credential;
  let baseUrl;
  let transport;
  if (choice.mode === 'local') {
    if (connection.model_id !== choice.model_id || typeof connection.socket_path !== 'string') {
      throw new ProviderError('local_connection_mismatch');
    }
    baseUrl = 'http://toddy.local/v1';
    const local = await unixFetch(connection.socket_path);
    transport = fetchImpl ?? local;
  } else {
    let url;
    try { url = new URL(connection.base_url); } catch { throw new ProviderError('invalid_provider_endpoint'); }
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
      throw new ProviderError('invalid_provider_endpoint');
    }
    baseUrl = url.href.replace(/\/$/, '');
    const send = fetchImpl ?? globalThis.fetch;
    transport = (input, init) => {
      const target = new URL(typeof input === 'string' || input instanceof URL ? input : input.url);
      if (target.origin !== url.origin || !target.pathname.startsWith(url.pathname.replace(/\/$/, '')+'/')) {
        throw new ProviderError('provider_origin_blocked');
      }
      return send(input, { ...init, redirect: 'manual' });
    };
  }
  // Import only the selected protocol, not provider discovery/OAuth/all registries.
  const { stream } = await import(`@earendil-works/pi-ai/api/${adapter.api}`);
  const model = Object.freeze({ id: choice.model_id, name: record.name ?? choice.model_id,
    ...adapter, baseUrl, reasoning: false, input: ['text'],
    contextWindow: budget.max_context_tokens, maxTokens: budget.max_output_tokens,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 } });
  let active;
  let requests = 0;
  let toolCalls = 0;
  // A provider instance belongs to one pinned task, including all tool turns.
  const deadline = AbortSignal.timeout(budget.task_deadline_seconds*1000);
  const zeroUsage = () => ({ input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } });
  const errorMessage = (code, aborted) => ({ role: 'assistant', content: [], api: model.api,
    provider: model.provider, model: model.id, usage: zeroUsage(),
    stopReason: aborted ? 'aborted' : 'error', errorMessage: code, timestamp: Date.now() });
  return Object.freeze({ model,
    capabilities: Object.freeze({ adapter_id: choice.adapter_id, model_id: choice.model_id,
      context_tokens: budget.max_context_tokens, max_output_tokens: budget.max_output_tokens,
      remote_fallback: false, automatic_retries: 0, cost_estimate: null,
      input_context_check: choice.mode === 'local' ? 'exact-server-template-tokenizer' : 'configured-catalog-and-provider-errors' }),
    streamFn(_ignoredModel, context, options = {}) {
      const output = createAssistantMessageEventStream();
      const controller = new AbortController();
      const signals = [controller.signal, deadline, ...(options.signal ? [options.signal] : [])];
      const signal = AbortSignal.any(signals);
      const fail = code => {
        const aborted = signal.aborted;
        output.push({ type: 'error', reason: aborted ? 'aborted' : 'error', error: errorMessage(code, aborted) });
      };
      if (signal.aborted) {
        fail(deadline.aborted ? 'provider_deadline' : 'canceled');
        return output;
      }
      if (active || requests >= budget.max_tool_calls+1) {
        fail(active ? 'provider_busy' : 'provider_request_limit');
        return output;
      }
      const lease = Symbol('provider-request');
      active = lease;
      requests++;
      queueMicrotask(async () => {
        let status;
        let fetchCount = 0;
        let received = 0;
        let textBytes = 0;
        let terminal = false;
        let transportCode;
        try {
          const fetch = async (input, init) => {
            try {
            if (++fetchCount !== 1) throw new ProviderError('provider_retry_blocked');
            if (choice.mode === 'local') {
              const request = new Request(input, init);
              const body = await request.clone().text();
              if (Buffer.byteLength(body) > 1048576) throw new ProviderError('provider_input_limit');
              const preflightHeaders = new Headers(request.headers);
              preflightHeaders.delete('content-length');
              preflightHeaders.delete('transfer-encoding');
              const headers = Object.fromEntries(preflightHeaders);
              // Pinned server uses the same chat/tool parser here as generation.
              const rendered = await boundedJson(await transport('http://toddy.local/apply-template',
                { method: 'POST', headers, body, signal }));
              if (typeof rendered.prompt !== 'string') throw new ProviderError('local_template_unsupported');
              const counted = await boundedJson(await transport('http://toddy.local/tokenize',
                { method: 'POST', headers, signal,
                  body: JSON.stringify({ content: rendered.prompt, add_special: true, parse_special: true }) }));
              if (!Array.isArray(counted.tokens) || counted.tokens.length+budget.max_output_tokens > budget.max_context_tokens) {
                throw new ProviderError('provider_context_limit');
              }
            }
            const response = await transport(input, init);
            status = response.status;
            if (!response.body) return response;
            const reader = response.body.getReader();
            return new Response(new ReadableStream({
              async pull(sink) {
                const item = await reader.read();
                if (item.done) { sink.close(); return; }
                received += item.value.byteLength;
                if (received > 4*1048576) {
                  transportCode = 'provider_response_limit';
                  await reader.cancel();
                  sink.error(new ProviderError('provider_response_limit'));
                } else sink.enqueue(item.value);
              },
              cancel(reason) { return reader.cancel(reason); },
            }), { status: response.status, statusText: response.statusText, headers: response.headers });
            } catch (error) {
              if (error instanceof ProviderError) {
                transportCode = error.code;
                if (integer(error.httpStatus, 100, 599)) status = error.httpStatus;
              }
              throw error;
            }
          };
          const inner = stream(model, context, { apiKey: credential, signal, fetch,
            maxTokens: budget.max_output_tokens, timeoutMs: budget.task_deadline_seconds*1000,
            maxRetries: 0, maxRetryDelayMs: 0, transport: 'sse', cacheRetention: 'none',
            ...(choice.mode === 'local' ? { temperature: 0,
              samplingParams: { chat_template_kwargs: { enable_thinking: false } } } : {}) });
          for await (const event of inner) {
            if (event.type === 'error') {
              // Explicit developer-fixture observation only. Default runtime
              // diagnostics remain classified; never forward a credential.
              fixtureObserver?.({ status: status ?? null,
                message: String(event.error.errorMessage ?? '').replaceAll(credential, '[credential]').slice(0, 2048) });
              throw new ProviderError('provider_failed');
            }
            if (event.type === 'text_delta') textBytes += Buffer.byteLength(event.delta);
            if (event.type === 'toolcall_end' && (++toolCalls > budget.max_tool_calls ||
                Buffer.byteLength(JSON.stringify(event.toolCall)) > 65536)) {
              throw new ProviderError('provider_tool_limit');
            }
            if (textBytes > 262144 || output.queue.length >= 32) {
              throw new ProviderError('provider_output_limit');
            }
            if (event.type === 'done') {
              terminal = true;
              if (active === lease) active = undefined;
            }
            output.push(event);
            if (terminal) break;
          }
          if (!terminal) throw new ProviderError('provider_incomplete');
        } catch (error) {
          const code = signal.aborted ? (deadline.aborted ? 'provider_deadline' : 'canceled') :
            status === 401 || status === 403 ? 'provider_auth_denied' :
            status === 429 ? 'provider_rate_limited' : transportCode ??
            (error instanceof ProviderError ? error.code : 'provider_unavailable');
          fail(code);
        } finally {
          // Completed streams must not abort a reused HTTP connection or clear
          // the lease of a tool-followup request already started by the agent.
          if (!terminal) controller.abort();
          if (active === lease) active = undefined;
        }
      });
      return output;
    },
  });
}
