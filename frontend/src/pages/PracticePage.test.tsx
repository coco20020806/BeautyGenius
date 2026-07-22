import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PracticePage } from './PracticePage';

test('renders tutorial steps from mock service', async () => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-practice' }));
  render(
    <MemoryRouter>
      <PracticePage />
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '跟练教程' })).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByText('橘朵腮红01')).toBeInTheDocument();
  });
  expect(screen.getByRole('button', { name: '前往示例图' })).toBeInTheDocument();
  expect(screen.getByText('全脸均匀铺开')).toBeInTheDocument();
  expect(screen.getByText('少量轻拍晕染')).toBeInTheDocument();
  expect(screen.getByText('珂岸面部素颜霜')).toBeInTheDocument();
  expect(screen.getByText('全脸推开')).toBeInTheDocument();
});

test('shows empty state without task id', async () => {
  sessionStorage.removeItem('makeupTask');
  render(
    <MemoryRouter>
      <PracticePage />
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '暂无跟练教程' })).toBeInTheDocument();
});
