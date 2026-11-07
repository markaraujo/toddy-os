import assert from 'node:assert/strict';
import { test } from 'node:test';
import { Readable } from 'node:stream';
import { strictJSON, readFrames, MAX_FRAME } from './framing.mjs';

test('strict strings, arrays, safe scalars and non-prototype object keys', () => {
  const object = strictJSON('{"__proto__":1,"text":"\\ud83d\\udc36","list":[true,false,null,-2,0.25]}');
  assert.equal(Object.getPrototypeOf(object), null);
  assert.equal(object.__proto__, 1);
  assert.equal(object.text, '🐶');
  assert.deepEqual(object.list, [true, false, null, -2, 0.25]);
});
test('duplicate keys include escaped equivalents and nested objects', () => {
  for (const text of ['{"k":1,"\\u006b":2}', '{"outer":{"k":1,"k":2}}'])
    assert.throws(() => strictJSON(text), /duplicate_json_key/);
});
test('invalid, nonfinite, unsafe, surrogate and trailing JSON fail closed', () => {
  for (const text of ['NaN', 'Infinity', '1e999', '9007199254740992', '01', '[1,]', '{"x":1,}',
    '"\\ud800"', '"\\udc00"', '{} garbage', '"unterminated']) assert.throws(() => strictJSON(text));
  assert.throws(() => strictJSON('['.repeat(66) + '0' + ']'.repeat(66)), /json_depth/);
});
test('fragmented and combined frames decode in order', async () => {
  const frame = text => { const body = Buffer.from(text); const header = Buffer.alloc(4); header.writeUInt32BE(body.length); return Buffer.concat([header, body]); };
  const bytes = Buffer.concat([frame('{"kind":"hello"}'), frame('{"kind":"done"}')]);
  const messages = [];
  for await (const message of readFrames(Readable.from([bytes.subarray(0, 2), bytes.subarray(2, 11), bytes.subarray(11)]))) messages.push(message.kind);
  assert.deepEqual(messages, ['hello', 'done']);
});
test('oversized, truncated and invalid UTF-8 frames fail', async () => {
  const oversized = Buffer.alloc(4); oversized.writeUInt32BE(MAX_FRAME + 1);
  for (const bytes of [oversized, Buffer.from([0, 0, 0]), Buffer.from([0, 0, 0, 2, 0xff, 0xff]), Buffer.from([0, 0, 0, 3, 123])]) {
    await assert.rejects(async () => { for await (const _ of readFrames(Readable.from([bytes]))) {} });
  }
});
