import { act, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, vi } from 'vitest';
import { MixGeneratingPage } from './MixGeneratingPage';

afterEach(() => vi.useRealTimers());

test('returns to mix selection when decisions are missing', () => {
  sessionStorage.removeItem('makeupMixDecision');
  render(<MemoryRouter initialEntries={['/mix/generating']}><Routes><Route path="/mix/generating" element={<MixGeneratingPage />} /><Route path="/library" element={<h1>混搭选择</h1>} /></Routes></MemoryRouter>);

  expect(screen.getByRole('heading', { name: '混搭选择' })).toBeInTheDocument();
});

test('visualizes generation and opens the preset result', async () => {
  vi.useFakeTimers();
  sessionStorage.setItem('makeupMixDecision', JSON.stringify({ base: null, eyes: 'eyes-rose', blush: null, contour: null, lips: 'lips-rose' }));
  render(<MemoryRouter initialEntries={['/mix/generating']}><Routes><Route path="/mix/generating" element={<MixGeneratingPage />} /><Route path="/mix/preview" element={<h1>混搭效果预览</h1>} /></Routes></MemoryRouter>);

  expect(screen.getByRole('progressbar', { name: '生成进度' })).toBeInTheDocument();
  expect(screen.getByText('匹配预制妆效')).toBeInTheDocument();
  await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
  expect(screen.getByRole('heading', { name: '混搭效果预览' })).toBeInTheDocument();
});
