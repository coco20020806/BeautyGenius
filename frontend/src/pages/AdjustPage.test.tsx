import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, vi } from 'vitest';
import { AdjustPage } from './AdjustPage';

vi.mock('../services/makeupService', () => ({
  makeupService: {
    saveAdjustment: vi.fn(async () => ({ taskId: 'task_real', status: 'completed' })),
  },
}));

vi.mock('../services/learningService', () => ({
  learningService: {
    saveAdjustment: vi.fn(async () => ({
      id: 'tutorial-adjusted',
      title: '微调方案',
      difficulty: '新手',
      duration: '约 10 分钟',
      mode: 'beginner',
      steps: [],
    })),
  },
}));

beforeEach(() => {
  sessionStorage.clear();
});

test('with taskId submits adjustment and navigates to practice', async () => {
  const { makeupService } = await import('../services/makeupService');
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task_real' }));
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={['/adjust']}>
      <Routes>
        <Route path="/adjust" element={<AdjustPage />} />
        <Route path="/practice" element={<h1>跟练页</h1>} />
        <Route path="/tutorial" element={<h1>图示教程</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(screen.getByRole('button', { name: '生成方案' }));
  expect(makeupService.saveAdjustment).toHaveBeenCalledWith(
    'task_real',
    expect.objectContaining({ skinType: '混合性肌肤' }),
  );
  await waitFor(() => {
    expect(screen.getByRole('heading', { name: '跟练页' })).toBeInTheDocument();
  });
});

test('without taskId keeps learning flow to tutorial', async () => {
  const { learningService } = await import('../services/learningService');
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={[{ pathname: '/adjust', state: { from: '/mix/preview', baseTutorialId: 'preset-1' } }]}>
      <Routes>
        <Route path="/adjust" element={<AdjustPage />} />
        <Route path="/practice" element={<h1>跟练页</h1>} />
        <Route path="/tutorial" element={<h1>图示教程</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(screen.getByRole('button', { name: '生成方案' }));
  expect(learningService.saveAdjustment).toHaveBeenCalled();
  await waitFor(() => {
    expect(screen.getByRole('heading', { name: '图示教程' })).toBeInTheDocument();
  });
});
