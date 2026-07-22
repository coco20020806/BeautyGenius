import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HomeExitButton } from './HomeExitButton';

function renderWithRoute(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={<h1>上传教程</h1>} />
        <Route path="/preview" element={<h1>妆效预览</h1>} />
        <Route path="/practice" element={<h1>跟练教程</h1>} />
      </Routes>
      <HomeExitButton />
    </MemoryRouter>,
  );
}

test('hides on the home page', () => {
  renderWithRoute('/');
  expect(screen.queryByRole('button', { name: /回到首页/ })).not.toBeInTheDocument();
});

test('shows on other pages and ends the flow when clicked', async () => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-1' }));
  sessionStorage.setItem('makeupProgress', JSON.stringify({ progress: 40 }));

  renderWithRoute('/preview');

  const button = screen.getByRole('button', { name: /回到首页/ });
  expect(button).toBeInTheDocument();

  await userEvent.click(button);

  expect(await screen.findByRole('heading', { name: '上传教程' })).toBeInTheDocument();
  expect(sessionStorage.getItem('makeupTask')).toBeNull();
  expect(sessionStorage.getItem('makeupProgress')).toBeNull();
});
