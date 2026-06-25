import { describe, expect, it } from 'vitest';
import { shortId } from '../lib/utils';

describe('utils', () => {
  it('shortens ids', () => {
    expect(shortId('abcdefghi')).toBe('abcdefgh');
  });
});
