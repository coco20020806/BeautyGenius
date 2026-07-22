import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LibraryPage } from './LibraryPage';

function renderMixPage() {
  return render(
    <MemoryRouter initialEntries={['/library?tab=mix']}>
      <Routes>
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/mix/generating" element={<h1>生成妆效中</h1>} />
      </Routes>
    </MemoryRouter>,
  );
}

test('starts collapsed and treats untouched parts as skipped', async () => {
  const user = userEvent.setup();
  renderMixPage();

  expect(screen.queryByRole('img', { name: '混搭妆容预览' })).not.toBeInTheDocument();
  const eyes = screen.getByRole('button', { name: '展开眼妆选项' });
  expect(screen.queryByRole('button', { name: '清透玫瑰眼妆' })).not.toBeInTheDocument();
  expect(screen.queryByText(/默认跳过|已展开|待选择|跳过此部位/)).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: '生成效果' })).toBeEnabled();

  await user.click(eyes);
  expect(await screen.findByRole('button', { name: '清透玫瑰眼妆' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '收起眼妆选项' }));
  expect(screen.queryByRole('button', { name: '清透玫瑰眼妆' })).not.toBeInTheDocument();
});

test('shows the chosen asset and generates null for untouched parts', async () => {
  const user = userEvent.setup();
  renderMixPage();

  await user.click(screen.getByRole('button', { name: '展开眼妆选项' }));
  await user.click(await screen.findByRole('button', { name: '清透玫瑰眼妆' }));
  expect(screen.getByRole('button', { name: '收起眼妆选项' })).toHaveTextContent('清透玫瑰眼妆');
  await user.click(screen.getByRole('button', { name: '生成效果' }));

  expect(JSON.parse(sessionStorage.getItem('makeupMixDecision') ?? '{}')).toEqual({ base: null, eyes: 'eyes-rose', blush: null, contour: null, lips: null });
  expect(screen.getByRole('heading', { name: '生成妆效中' })).toBeInTheDocument();
});
