// B03 native integration fixture: real Pi Agent/provider, one actual owned file.
import { readFileSync, closeSync, constants } from 'node:fs';
import { open, writeFile } from 'node:fs/promises';
import { Agent } from '@earendil-works/pi-agent-core';
import { createProvider, ProviderError } from './provider.mjs';
import { unixFetch } from './local-transport.mjs';

const observed = { executions: 0, textEvents: 0, finalStop: null, providerCode: null, answerContainsFile: false };
try {
  const descriptor = Number(process.env.TODDY_CONNECTION_FD);
  if (!Number.isInteger(descriptor) || descriptor < 3) throw Error('private_connection_missing');
  const bytes = readFileSync(descriptor);
  closeSync(descriptor);
  if (bytes.length > 65536) throw Error('private_connection_limit');
  const connection = JSON.parse(bytes);
  const modelId = 'toddy-qwen3-1.7b-q8_0';
  const profile = { schema_version: 1,
    provider: { mode: 'local', adapter_id: 'local-llama-cpp', model_id: modelId,
      connection_ref: 'local-native', allow_remote_fallback: false },
    budgets: { max_context_tokens: 4096, max_output_tokens: 256, task_deadline_seconds: 60,
      max_tool_calls: 2, max_retries: 0, remote_spending_enabled: false } };
  const send = await unixFetch(connection.socket_path);
  const provider = await createProvider(profile, { ...connection, id: 'local-native' }, {
    [modelId]: { adapter_id: 'local-llama-cpp', qualified: true,
      context_tokens: 4096, max_output_tokens: 1024 } }, {
    fixtureObserver: diagnostic => {
      // All content in this fixture is synthetic; no owner profile is loaded.
      writeFile('/build/sdk-error.json', JSON.stringify(diagnostic), {mode:0o600}).catch(()=>{});
    },
    // This fixture contains only synthetic data. Preserve bounded private HTTP
    // failure diagnostics, stripping the actual ephemeral credential first.
    fetchImpl: async (...args) => {
      const response = await send(...args);
      if (response.status >= 400) {
        const text = (await response.clone().text()).replaceAll(connection.credential, '[credential]').slice(0, 4096);
        await writeFile('/build/provider-diagnostic.json', JSON.stringify({status:response.status, body:text}), {mode:0o600});
      }
      return response;
    },
  });
  let executions = 0;
  let actualContent;
  let textEvents = 0;
  const started = performance.now();
  const agent = new Agent({ streamFn: provider.streamFn,
    initialState: { model: provider.model,
      systemPrompt: 'You are testing an actual file tool. Call read_fixture exactly once for fixture.txt. Never guess file contents. After the tool returns, report its full contents unchanged. /no_think',
      tools: [{ name: 'read_fixture', label: 'Read disposable fixture',
        description: 'Read the actual disposable fixture.txt. Required before answering its contents.',
        parameters: { type: 'object', properties: { name: { type: 'string', enum: ['fixture.txt'] } },
          required: ['name'], additionalProperties: false }, executionMode: 'sequential', replay: 'never',
        execute: async (_id, args, signal) => {
          if (signal?.aborted || args.name !== 'fixture.txt' || ++executions !== 1) throw Error('fixture_tool_rejected');
          observed.executions = executions;
          const file = await open('/build/disposable/fixture.txt', constants.O_RDONLY | constants.O_NOFOLLOW);
          try {
            const info = await file.stat();
            if (!info.isFile() || info.size > 128) throw Error('fixture_file_rejected');
            actualContent = await file.readFile('utf8');
          } finally { await file.close(); }
          return { content: [{ type: 'text', text: actualContent }], details: { fixture: true } };
        } } ] } });
  agent.subscribe(event => {
    if (event.type === 'message_update' && event.assistantMessageEvent?.type === 'text_delta') textEvents++;
  });
  await agent.prompt('Use read_fixture to read fixture.txt, then report its full contents unchanged. /no_think');
  const final = agent.state.messages.findLast(message => message.role === 'assistant');
  const answer = final?.content.filter(block => block.type === 'text').map(block => block.text).join('');
  observed.textEvents = textEvents;
  observed.finalStop = final?.stopReason ?? null;
  observed.answerContainsFile = !!actualContent && !!answer?.includes(actualContent.trim());
  if (/^(provider_[a-z_]+|canceled)$/.test(final?.errorMessage ?? '')) observed.providerCode = final.errorMessage;
  if (executions !== 1 || !observed.answerContainsFile ||
      final.stopReason !== 'stop' || !textEvents) throw Error('actual_local_tool_postcondition_failed');
  console.log(JSON.stringify({ scope: 'native Pi Agent/local model/disposable file only; no executor/durable task/UI claim',
    actual_tool_executions: executions, actual_file_content_matched: true, text_delta_events: textEvents,
    elapsed_seconds: Math.round((performance.now()-started)/10)/100,
    model_id: modelId, api: provider.model.api, remote_fallback: false,
    automatic_retries: 0, cost_estimate: provider.capabilities.cost_estimate,
    final_stop_reason: final.stopReason,
    usage: { input_uncached: final.usage.input, cache_read: final.usage.cacheRead,
      cache_write: final.usage.cacheWrite, output: final.usage.output, total: final.usage.totalTokens } }));
} catch (error) {
  // Raw SDK errors/connection objects are private; only classified codes leave.
  const known = new Set(['actual_local_tool_postcondition_failed', 'fixture_tool_rejected',
    'fixture_file_rejected', 'private_connection_missing', 'private_connection_limit']);
  const frames = (error.stack ?? '').split('\n').slice(1)
    .flatMap(line => line.match(/(?:file:\/\/\/src\/|node:)[^\s)]+:\d+:\d+/g) ?? []).slice(0, 3);
  console.error(JSON.stringify({ code: error instanceof ProviderError ? error.code :
    known.has(error.message) ? error.message : 'local_tool_fixture_failed',
    error_type: error.constructor.name, observed, frames }));
  process.exitCode = 1;
}
