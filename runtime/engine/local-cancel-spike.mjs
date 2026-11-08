// Actual local provider Stop and pre-dispatch context rejection, no root tools.
import { readFileSync, closeSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { Agent } from '@earendil-works/pi-agent-core';
import { createProvider, ProviderError } from './provider.mjs';
import { unixFetch } from './local-transport.mjs';

const observed = {};
let stage = 'initialization';
try {
  const descriptor = Number(process.env.TODDY_CONNECTION_FD);
  const bytes = readFileSync(descriptor); closeSync(descriptor);
  if (bytes.length > 65536) throw Error('private_input_limit');
  const connection = JSON.parse(bytes);
  const modelId = connection.model_id;
  const catalog = { [modelId]: { adapter_id:'local-llama-cpp', qualified:true,
    context_tokens:4096, max_output_tokens:1024 } };
  const profile = (context=4096, output=512) => ({ schema_version:1,
    provider:{mode:'local',adapter_id:'local-llama-cpp',model_id:modelId,
      connection_ref:'local-native',allow_remote_fallback:false},
    budgets:{max_context_tokens:context,max_output_tokens:output,task_deadline_seconds:20,
      max_tool_calls:0,max_retries:0,remote_spending_enabled:false} });
  const privateConnection = {...connection,id:'local-native'};
  const observe = diagnostic => writeFile('/build/cancel-sdk-error.json',JSON.stringify({stage,...diagnostic}),{mode:0o600}).catch(()=>{});
  stage = 'cancellation';
  const provider = await createProvider(profile(),privateConnection,catalog,{fixtureObserver:observe});
  const agent = new Agent({streamFn:provider.streamFn,initialState:{model:provider.model,tools:[],
    systemPrompt:'Follow the request concisely. /no_think'}});
  let canceledAt;
  let deltas=0;
  agent.subscribe(event=>{
    if(event.type==='message_update' && event.assistantMessageEvent?.type==='text_delta') {
      deltas++;
      if(canceledAt===undefined) { canceledAt=performance.now(); agent.abort(); }
    }
  });
  await agent.prompt('Write an extremely long list of the integers from 1 to 1000. /no_think');
  const canceled=agent.state.messages.findLast(message=>message.role==='assistant');
  const elapsed=performance.now()-canceledAt;
  observed.cancelStop = canceled?.stopReason;
  observed.cancelCode = canceled?.errorMessage;
  if(canceledAt===undefined || canceled?.stopReason!=='aborted' || canceled.errorMessage!=='canceled' || elapsed>2000) {
    throw Error('active_model_cancel_failed');
  }
  stage = 'post-cancel';
  const follow=await createProvider(profile(512,32),privateConnection,catalog,{fixtureObserver:observe});
  const next=new Agent({streamFn:follow.streamFn,initialState:{model:follow.model,tools:[]}});
  const followStarted=performance.now();
  await next.prompt('Respond exactly READY. /no_think');
  const done=next.state.messages.findLast(message=>message.role==='assistant');
  const text=done?.content.filter(block=>block.type==='text').map(block=>block.text).join('');
  observed.followStop = done?.stopReason;
  observed.followCode = done?.errorMessage;
  observed.followContainsReady = text?.includes('READY');
  if(done?.stopReason!=='stop'||!observed.followContainsReady) throw Error('post_cancel_request_failed');
  const followElapsed=performance.now()-followStarted;
  let generationRequests=0;
  stage = 'context-limit';
  const send=await unixFetch(connection.socket_path);
  const bounded=await createProvider(profile(256,32),privateConnection,catalog,{fixtureObserver:observe,fetchImpl:async(input,init)=>{
    if(new URL(typeof input==='string'?input:input.url).pathname==='/v1/chat/completions') generationRequests++;
    return send(input,init);
  }});
  const long=new Agent({streamFn:bounded.streamFn,initialState:{model:bounded.model,tools:[]}});
  await long.prompt('context-limit-fixture '.repeat(1024));
  const rejected=long.state.messages.findLast(message=>message.role==='assistant');
  observed.contextStop = rejected?.stopReason;
  observed.contextCode = rejected?.errorMessage;
  observed.overbudgetRequests = generationRequests;
  if(rejected?.stopReason!=='error'||rejected.errorMessage!=='provider_context_limit'||generationRequests!==0) {
    throw Error('context_admission_failed');
  }
  console.log(JSON.stringify({scope:'native active inference cancellation/context admission only',
    cancel_after_text_delta:true,deltas_before_abort:deltas,cancel_latency_ms:Math.round(elapsed),
    stop_reason:canceled.stopReason,classified_code:canceled.errorMessage,
    post_cancel_ready:true,post_cancel_seconds:Math.round(followElapsed/10)/100,
    context_limit_code:rejected.errorMessage,overbudget_generation_requests:generationRequests,
    followup_usage:{input_uncached:done.usage.input,cache_read:done.usage.cacheRead,
      cache_write:done.usage.cacheWrite,output:done.usage.output,total:done.usage.totalTokens},
    remote_fallback:false,automatic_retries:0}));
} catch (error) {
  const known = new Set(['private_input_limit','active_model_cancel_failed','post_cancel_request_failed','context_admission_failed']);
  console.error(JSON.stringify({code:error instanceof ProviderError ? error.code :
    known.has(error.message) ? error.message : 'native_cancel_context_fixture_failed',stage,observed}));
  process.exitCode=1;
}
