import { describe, expect, it } from 'vitest';
import { formatRemainingSeconds } from '../utils/formatRemainingSeconds';

describe('formatRemainingSeconds', () => {
  it('formats sub-hour as m:ss', () => {
    expect(formatRemainingSeconds(125)).toBe('2:05');
    expect(formatRemainingSeconds(600)).toBe('10:00');
  });

  it('formats hour+ as Chinese phrase', () => {
    expect(formatRemainingSeconds(3700)).toBe('约 1 小时 1 分钟');
  });
});
