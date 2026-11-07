// Strict, bounded worker framing. No diagnostics or banners on protocol stdout.
export const MAX_FRAME = 1024 * 1024;

export function strictJSON(text) {
  let i = 0;
  const white = () => { while (/[\x20\t\r\n]/.test(text[i] ?? '\0')) i++; };
  function string() {
    const start = i++;
    while (i < text.length) {
      const c = text[i++];
      if (c === '\\') { i++; continue; }
      if (c === '"') {
        const result = JSON.parse(text.slice(start, i));
        for (let n = 0; n < result.length; n++) {
          const code = result.charCodeAt(n);
          if (code >= 0xd800 && code <= 0xdbff) {
            const next = result.charCodeAt(++n);
            if (!(next >= 0xdc00 && next <= 0xdfff)) throw Error('invalid_unicode');
          } else if (code >= 0xdc00 && code <= 0xdfff) throw Error('invalid_unicode');
        }
        return result;
      }
      if (c.charCodeAt(0) < 32) throw Error('invalid_json');
    }
    throw Error('truncated_json');
  }
  function value(depth = 0) {
    if (depth > 64) throw Error('json_depth');
    white();
    const c = text[i];
    if (c === '"') return string();
    if (c === '{' || c === '[') {
      i++;
      const object = c === '{';
      const result = object ? Object.create(null) : [];
      const seen = new Set();
      white();
      if (text[i] === (object ? '}' : ']')) { i++; return result; }
      while (true) {
        white();
        let key;
        if (object) {
          if (text[i] !== '"') throw Error('invalid_json_key');
          key = string();
          if (seen.has(key)) throw Error('duplicate_json_key');
          seen.add(key);
          white();
          if (text[i++] !== ':') throw Error('invalid_json');
        }
        const child = value(depth + 1);
        if (object) result[key] = child; else result.push(child);
        white();
        if (text[i] === (object ? '}' : ']')) { i++; return result; }
        if (text[i++] !== ',') throw Error('invalid_json');
      }
    }
    for (const [literal, result] of [['true', true], ['false', false], ['null', null]]) {
      if (text.startsWith(literal, i)) { i += literal.length; return result; }
    }
    const match = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(text.slice(i));
    if (!match) throw Error('invalid_json');
    i += match[0].length;
    const number = Number(match[0]);
    if (!Number.isFinite(number) || (Number.isInteger(number) && !Number.isSafeInteger(number))) throw Error('json_number_range');
    return number;
  }
  const result = value();
  white();
  if (i !== text.length) throw Error('trailing_json');
  return result;
}

export async function* readFrames(stream) {
  let pending = Buffer.alloc(0);
  const decoder = new TextDecoder('utf-8', { fatal: true });
  for await (const chunk of stream) {
    pending = Buffer.concat([pending, chunk]);
    while (pending.length >= 4) {
      const length = pending.readUInt32BE(0);
      if (length === 0 || length > MAX_FRAME) throw Error('frame_length');
      if (pending.length < length + 4) break;
      yield strictJSON(decoder.decode(pending.subarray(4, length + 4)));
      pending = pending.subarray(length + 4);
    }
    if (pending.length > MAX_FRAME + 4) throw Error('frame_length');
  }
  if (pending.length) throw Error('truncated_frame');
}

export function writeFrame(stream, message) {
  const body = Buffer.from(JSON.stringify(message), 'utf8');
  if (!body.length || body.length > MAX_FRAME) throw Error('frame_length');
  const header = Buffer.alloc(4);
  header.writeUInt32BE(body.length);
  return new Promise((resolve, reject) => stream.write(Buffer.concat([header, body]), error => error ? reject(error) : resolve()));
}
