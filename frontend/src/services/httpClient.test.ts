import { describe, expect, it, vi } from 'vitest';
import { HttpError, requestJson } from './httpClient';

describe('httpClient', () => {
  it('parses API error body', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ code: 'TASK_NOT_FOUND', message: '任务不存在', requestId: 'req_test' }),
      }),
    );

    await expect(requestJson('/api/v1/makeup/tasks/x/analysis')).rejects.toMatchObject({
      message: '任务不存在',
      status: 404,
      code: 'TASK_NOT_FOUND',
      requestId: 'req_test',
    } satisfies Partial<HttpError>);

    vi.unstubAllGlobals();
  });
});
