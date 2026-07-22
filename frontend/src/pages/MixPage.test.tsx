import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { LibraryPage } from './LibraryPage';

function renderMixPage() {
  return render(
    <MemoryRouter initialEntries={['/library?tab=mix']}>
      <Routes>
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/tutorial" element={<h1>图示教程</h1>} />
      </Routes>
    </MemoryRouter>,
  );
}

test('shows library parts as checkable modules and disables generate until selected', async () => {
  const user = userEvent.setup();
  renderMixPage();

  expect(await screen.findByRole('button', { name: '勾选眼妆' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '勾选修容' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '勾选唇妆' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /勾选底妆|勾选腮红/ })).not.toBeInTheDocument();
  expect(screen.getByRole('img', { name: '清透玫瑰眼妆封面' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '生成图示流程' })).toBeDisabled();

  await user.click(screen.getByRole('button', { name: '勾选眼妆' }));
  expect(screen.getByRole('button', { name: '取消勾选眼妆' })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByRole('button', { name: '生成图示流程' })).toBeEnabled();
});

test('generates an illustrated flow from checked parts in order', async () => {
  const user = userEvent.setup();
  renderMixPage();

  await user.click(await screen.findByRole('button', { name: '勾选眼妆' }));
  await user.click(screen.getByRole('button', { name: '勾选唇妆' }));
  await user.click(screen.getByRole('button', { name: '生成图示流程' }));

  expect(JSON.parse(sessionStorage.getItem('makeupMixDecision') ?? '{}')).toEqual({
    base: null,
    eyes: 'eyes-rose',
    blush: null,
    contour: null,
    lips: 'lips-rose',
  });
  expect(await screen.findByRole('heading', { name: '图示教程' })).toBeInTheDocument();
});
