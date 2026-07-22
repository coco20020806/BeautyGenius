import { collectAnalysis, makeupService } from './makeupService';

test('rejects unsupported video files', async () => {
  const file = new File(['x'], 'tutorial.txt', { type: 'text/plain' });

  await expect(makeupService.uploadVideo(file)).rejects.toThrow('仅支持 MP4 或 MOV 视频');
});

test('progress reaches preview-ready state', async () => {
  const states = await collectAnalysis(makeupService.analyze('task-1'));

  expect(states.at(-1)).toMatchObject({ progress: 100, status: 'completed' });
  expect(states).toHaveLength(4);
});
