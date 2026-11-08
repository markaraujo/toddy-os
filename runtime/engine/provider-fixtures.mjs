// Offline protocol contracts against the pinned SDK, never live provider acceptance.
import assert from 'node:assert/strict';
import { normalizeContext } from '@earendil-works/pi-ai/utils/transcript';
import { createProvider } from './provider.mjs';
const originalFetch = globalThis.fetch;
globalThis.fetch = () => { throw Error('external_network_forbidden'); };
const credential = 'synthetic-fixture-not-a-key';
const families = ['openai-compatible','openai','anthropic','openrouter'];
const context = normalizeContext({ messages:[{role:'user',content:'Fixture only',timestamp:0}],
  tools:[{name:'read_fixture',description:'Read disposable fixture',parameters:{type:'object',properties:{name:{type:'string'}},required:['name']}}] });
const event = (type, fields) => ({type,...fields});
function frames(family, tool=false) {
  if (family === 'anthropic') return [
    event('message_start',{message:{id:'fixture',model:'fixture-model',usage:{input_tokens:10,output_tokens:0},content:[],role:'assistant',type:'message'}}),
    event('content_block_start',{index:0,content_block:tool?{type:'tool_use',id:'call-fixture',name:'read_fixture',input:{}}:{type:'text',text:''}}),
    event('content_block_delta',{index:0,delta:tool?{type:'input_json_delta',partial_json:'{"name":"é.txt"}'}:{type:'text_delta',text:'Olá 世界'}}),
    event('content_block_stop',{index:0}),event('message_delta',{delta:{stop_reason:tool?'tool_use':'end_turn'},usage:{output_tokens:3}}),event('message_stop',{})];
  if (family === 'openai') {
    const item = tool?{type:'function_call',id:'fc_fixture',call_id:'call-fixture',name:'read_fixture',arguments:''}:
      {type:'message',id:'msg_fixture',role:'assistant',content:[],status:'in_progress'};
    const complete = tool?{...item,arguments:'{"name":"é.txt"}',status:'completed'}:
      {...item,content:[{type:'output_text',text:'Olá 世界',annotations:[]}],status:'completed'};
    return [event('response.created',{response:{id:'resp_fixture',status:'in_progress'}}),
      event('response.output_item.added',{output_index:0,item}),
      event(tool?'response.function_call_arguments.delta':'response.output_text.delta',
        {output_index:0,item_id:item.id,content_index:0,delta:tool?'{"name":"é.txt"}':'Olá 世界'}),
      event('response.output_item.done',{output_index:0,item:complete}),
      event('response.completed',{response:{id:'resp_fixture',status:'completed',output:[complete],usage:{input_tokens:10,output_tokens:3,total_tokens:13,input_tokens_details:{cached_tokens:0}}}})];
  }
  const chunk = (delta, finish_reason=null) => ({id:'fixture',object:'chat.completion.chunk',model:'fixture-model',created:0,choices:[{index:0,delta,finish_reason}]});
  return [chunk({role:'assistant',...(tool?{tool_calls:[{index:0,id:'call-fixture',type:'function',function:{name:'read_fixture',arguments:''}}]}:{content:''})}),
    chunk(tool?{tool_calls:[{index:0,function:{arguments:'{"name":"é.txt"}'}}]}:{content:'Olá 世界'}),
    {...chunk({},tool?'tool_calls':'stop'),usage:{prompt_tokens:10,completion_tokens:3,total_tokens:13}},'[DONE]'];
}
function response(family, values, {hold=false, signal}={}) {
  const wire = values.map(value=>value==='[DONE]'?'data: [DONE]\n\n':
    `${family==='anthropic'||family==='openai'?`event: ${value.type}\n`:''}data: ${JSON.stringify(value)}\n\n`).join('');
  const bytes = new TextEncoder().encode(wire);
  let offset=0;
  return new Response(new ReadableStream({
    async pull(sink) {
      if(offset<bytes.length) { const end=Math.min(offset+(bytes.length>100000?8192:7),bytes.length);sink.enqueue(bytes.slice(offset,end));offset=end;return; }
      if(!hold) {sink.close();return;}
      await new Promise(resolve=>{if(signal.aborted)resolve();else signal.addEventListener('abort',resolve,{once:true});});
      sink.error(new DOMException('Canceled','AbortError'));
    },
  }),{headers:{'content-type':'text/event-stream'}});
}
function settings(family) {
  return {schema_version:1,provider:{mode:'remote',adapter_id:family,model_id:'fixture-model',connection_ref:'fixture',allow_remote_fallback:false},
    budgets:{max_context_tokens:4096,max_output_tokens:64,task_deadline_seconds:5,max_tool_calls:1,max_retries:0,remote_spending_enabled:true}};
}
async function setup(family, send, mutate=()=>{}) {
  const profile=settings(family);mutate(profile);
  return createProvider(profile,{id:'fixture',base_url:'https://provider.invalid/v1',credential},
    {'fixture-model':{adapter_id:family,qualified:true,context_tokens:4096,max_output_tokens:64}},
    {remoteConsent:true,fetchImpl:send});
}
async function consume(provider, options={}, onEvent=()=>{}) {
  const events=[];
  for await(const item of provider.streamFn(provider.model,context,options)) {events.push(item);onEvent(item);}
  assert.equal(events.filter(e=>['error','done'].includes(e.type)).length,1);
  return {events,last:events.at(-1)};
}
const results=[];
// Synthetic streams have no socket handle to keep Node alive for deadline delivery.
const keepAlive=setInterval(()=>{},1000);
try {
  for(const family of families) {
    let calls=0;
    const requests=[];
    const provider=await setup(family,async(input,init)=>{
      calls++;assert.equal(init.redirect,'manual');
      const request=new Request(input,init);requests.push(JSON.parse(await request.text()));
      assert.equal(new URL(request.url).origin,'https://provider.invalid');
      assert.equal(request.headers.get(family==='anthropic'?'x-api-key':'authorization'),family==='anthropic'?credential:`Bearer ${credential}`);
      return response(family,frames(family,calls===2));
    });
    const text=await consume(provider);
    assert.equal(text.last.type,'done');
    assert.equal(text.last.message.content.filter(b=>b.type==='text').map(b=>b.text).join(''),'Olá 世界');
    assert.ok(text.events.some(e=>e.type==='text_delta'&&e.delta.includes('Olá')));
    assert.equal(text.last.message.usage.totalTokens,13);
    const tool=await consume(provider);
    assert.equal(tool.last.type,'done');assert.equal(tool.last.reason,'toolUse');
    const call=tool.last.message.content.find(b=>b.type==='toolCall');
    assert.equal(call.name,'read_fixture');assert.deepEqual(call.arguments,{name:'é.txt'});
    assert.equal((await consume(provider)).last.error.errorMessage,'provider_request_limit');
    assert.equal(calls,2);assert.equal(provider.capabilities.cost_estimate,null);
    assert.ok(requests.every(r=>r.stream===true));
    for(const status of [401,429,302]) {
      let attempts=0;
      const failing=await setup(family,async()=>{attempts++;return new Response(JSON.stringify({error:{message:credential}}),
        {status,headers:{'content-type':'application/json','location':'https://other.invalid/'}});});
      const failed=await consume(failing);
      assert.equal(failed.last.type,'error');
      if(status!==302) assert.equal(failed.last.error.errorMessage,status===401?'provider_auth_denied':'provider_rate_limited');
      assert.ok(!JSON.stringify(failed).includes(credential));assert.equal(attempts,1);
    }
    const truncated=await setup(family,async()=>response(family,frames(family).slice(0,2)));
    assert.equal((await consume(truncated)).last.type,'error');
    const malformed=await setup(family,async()=>new Response('event: message_start\ndata: {broken\n\n',{headers:{'content-type':'text/event-stream'}}));
    assert.equal((await consume(malformed)).last.type,'error');
    const controller=new AbortController();let cancels=0;
    const cancel=await setup(family,async(_input,init)=>{cancels++;return response(family,frames(family).slice(0,3),{hold:true,signal:init.signal});});
    const canceled=await consume(cancel,{signal:controller.signal},item=>{if(item.type==='text_delta')controller.abort();});
    assert.equal(canceled.last.error.errorMessage,'canceled');assert.equal(canceled.last.reason,'aborted');assert.equal(cancels,1);
    let started;
    const waiting=new Promise(resolve=>{started=resolve;});const release=new AbortController();
    const busy=await setup(family,async(_input,init)=>{started();return response(family,frames(family).slice(0,3),{hold:true,signal:init.signal});});
    const running=consume(busy,{signal:release.signal});await waiting;
    assert.equal((await consume(busy)).last.error.errorMessage,'provider_busy');release.abort();await running;
    const noTools=await setup(family,async()=>response(family,frames(family,true)),p=>p.budgets.max_tool_calls=0);
    assert.equal((await consume(noTools)).last.error.errorMessage,'provider_tool_limit');
    const huge=JSON.parse(JSON.stringify(frames(family)).replaceAll('Olá 世界','x'.repeat(270000)));
    const oversized=await setup(family,async()=>response(family,huge));
    assert.equal((await consume(oversized)).last.error.errorMessage,'provider_output_limit');
    let forbidden=0;
    for(const [change,code] of [[p=>p.provider.mode='deferred','backend_deferred'],[p=>p.budgets.remote_spending_enabled=false,'remote_consent_required'],
      [p=>p.provider.allow_remote_fallback=true,'remote_fallback_blocked'],[p=>p.provider.model_id='unknown','model_unavailable']]) {
      await assert.rejects(setup(family,async()=>{forbidden++;throw Error('unexpected_dispatch');},change),e=>e.code===code);
    }
    assert.equal(forbidden,0);
    results.push({family,scope:'synthetic protocol only; live-unverified',text_unicode_fragmented:true,structured_tool:true,usage:true,
      auth_rate_redirect_no_retry:true,truncated_malformed_rejected:true,active_cancel:true,busy_request_limit:true,output_tool_limits:true,pre_dispatch_policy:true});
  }
  const deadline=await setup('openai',async(_input,init)=>response('openai',frames('openai').slice(0,3),{hold:true,signal:init.signal}),p=>p.budgets.task_deadline_seconds=1);
  const expired=await consume(deadline);
  assert.equal(expired.last.error.errorMessage,'provider_deadline');
  console.log(JSON.stringify({schema_version:1,scope:'offline pinned Pi 1.5.0 protocol fixtures; no paid calls, no live provider qualification',task_deadline:true,results}));
} finally {clearInterval(keepAlive);globalThis.fetch=originalFetch;}
