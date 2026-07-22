import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, vi } from 'vitest';
import { PreviewPage } from './PreviewPage';
import { UploadPage } from './UploadPage';
import { makeupService } from '../services/makeupService';

afterEach(() => {
  vi.restoreAllMocks();
});

test('shows comparison, makeup summary and suitability decisions', async () => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-1' }));
  render(<MemoryRouter><PreviewPage /></MemoryRouter>);

  expect(await screen.findByRole('heading', { name: '适配预览' })).toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole('slider', { name: '妆前妆后对比位置' })).toBeInTheDocument());
  expect(screen.getByText('约 1 分钟')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '适合我' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '需要微调' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '不适合我' })).not.toBeInTheDocument();
});

test('shows generation failure when afterImage is missing', async () => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-1' }));
  vi.spyOn(makeupService, 'getPreview').mockResolvedValue({
    taskId: 'task-1',
    title: '清透玫瑰通勤妆',
    style: '清透自然',
    occasion: '通勤 · 日常',
    difficulty: '新手友好',
    duration: '约 1 分钟',
    beforeImage: 'before.jpg',
    afterImage: null,
    generationFailed: true,
    generationFailureReason: '妆容预览已跳过，未生成适配图',
    palette: ['#ead6cf'],
    hints: [
      {
        title: '妆容生成失败',
        description: '妆容预览已跳过，未生成适配图',
        tone: 'adjust',
      },
    ],
  });

  render(<MemoryRouter><PreviewPage /></MemoryRouter>);

  expect(await screen.findByRole('region', { name: '妆容生成失败' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { level: 2, name: '妆容生成失败' })).toBeInTheDocument();
  expect(screen.getAllByText('妆容预览已跳过，未生成适配图').length).toBeGreaterThan(0);
  expect(screen.queryByRole('slider', { name: '妆前妆后对比位置' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '适合我' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: '重新上传' })).toBeInTheDocument();
});

test('darker intensity swatch raises after-makeup opacity', async () => {
  const user = userEvent.setup();
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-1' }));
  const { container } = render(<MemoryRouter><PreviewPage /></MemoryRouter>);

  await screen.findByRole('heading', { name: '适配预览' });
  const afterLayer = () => container.querySelector('.comparison__after') as HTMLElement;

  expect(afterLayer().style.opacity).toBe('0.8');

  await user.click(screen.getByRole('button', { name: '妆容浓淡 L1' }));
  expect(afterLayer().style.opacity).toBe('0.2');

  await user.click(screen.getByRole('button', { name: '妆容浓淡 L5' }));
  expect(afterLayer().style.opacity).toBe('1');
  expect(screen.getByRole('button', { name: '妆容浓淡 L5' })).toHaveAttribute('aria-pressed', 'true');
});

test('navigates to practice when accepting the look', async () => {
  const user = userEvent.setup();
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-1' }));
  render(
    <MemoryRouter initialEntries={['/preview']}>
      <Routes>
        <Route path="/preview" element={<PreviewPage />} />
        <Route path="/practice" element={<h1>跟练教程</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  await screen.findByRole('heading', { name: '适配预览' });
  await user.click(screen.getByRole('button', { name: '适合我' }));
  expect(await screen.findByRole('heading', { name: '跟练教程' })).toBeInTheDocument();
});

test('routes adjust decision into adjustment page', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/preview']}>
      <Routes>
        <Route path="/preview" element={<PreviewPage />} />
        <Route path="/adjust" element={<h1>微调设置</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(await screen.findByRole('button', { name: '需要微调' }));

  expect(screen.getByRole('heading', { name: '微调设置' })).toBeInTheDocument();
});

test('returns directly to video upload instead of revisiting parsing', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/parsing', '/preview']} initialIndex={1}>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/parsing" element={<h1>解析中</h1>} />
        <Route path="/preview" element={<PreviewPage />} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(screen.getByRole('button', { name: '返回' }));

  expect(screen.getByRole('heading', { name: '上传教程' })).toBeInTheDocument();
});
