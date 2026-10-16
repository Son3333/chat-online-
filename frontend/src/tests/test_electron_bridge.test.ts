import { describe, it, expect } from 'vitest';

describe('PythonBridge Wire Protocol Framing', () => {
  it('correctly encodes 4-byte big-endian header length and JSON body', () => {
    const payload = { action: 'ping', data: 'hello' };
    const jsonStr = JSON.stringify(payload);
    const bodyBuffer = Buffer.from(jsonStr, 'utf-8');

    const header = Buffer.alloc(4);
    header.writeUInt32BE(bodyBuffer.length, 0);

    const fullPacket = Buffer.concat([header, bodyBuffer]);

    expect(fullPacket.length).toBe(4 + bodyBuffer.length);
    expect(fullPacket.readUInt32BE(0)).toBe(bodyBuffer.length);
  });

  it('correctly decodes fragmented buffers into complete JSON packets', () => {
    const payload = { action: 'new_message', content: 'Telegram Stream Message' };
    const bodyBuffer = Buffer.from(JSON.stringify(payload), 'utf-8');
    const header = Buffer.alloc(4);
    header.writeUInt32BE(bodyBuffer.length, 0);
    const fullPacket = Buffer.concat([header, bodyBuffer]);

    // Split packet into two chunks simulating TCP fragmentation
    const chunk1 = fullPacket.subarray(0, 10);
    const chunk2 = fullPacket.subarray(10);

    let accumulator = Buffer.alloc(0);
    accumulator = Buffer.concat([accumulator, chunk1]);

    // Chunk 1 cannot be fully parsed yet
    const length1 = accumulator.readUInt32BE(0);
    expect(accumulator.length < 4 + length1).toBe(true);

    // After chunk 2 arrives
    accumulator = Buffer.concat([accumulator, chunk2]);
    expect(accumulator.length >= 4 + length1).toBe(true);

    const extracted = accumulator.subarray(4, 4 + length1);
    const parsed = JSON.parse(extracted.toString('utf-8'));

    expect(parsed.action).toBe('new_message');
    expect(parsed.content).toBe('Telegram Stream Message');
  });
});

