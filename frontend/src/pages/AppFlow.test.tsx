import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../App';

test('completes the MVP flow by skipping photo upload', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/']}><AppRoutes /></MemoryRouter>);

  await user.upload(
    screen.getByLabelText('选择教程视频'),
    new File(['tutorial'], 'tutorial.mp4', { type: 'video/mp4' }),
  );
  await user.click(screen.getByRole('button', { name: '下一步' }));
  await user.click(await screen.findByRole('button', { name: '暂时跳过' }, { timeout: 10000 }));

  await waitFor(() => expect(screen.getByRole('heading', { name: '适配预览' })).toBeInTheDocument(), { timeout: 15000 });
  expect(await screen.findByRole('slider', { name: '妆前妆后对比位置' })).toBeInTheDocument();
}, 20000);

test('keeps bottom navigation on top-level destinations', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/']}><AppRoutes /></MemoryRouter>);

  await user.click(screen.getByRole('link', { name: /知识库/ }));

  expect(screen.getByText('MY BEAUTY ARCHIVE')).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: '主导航' })).toBeInTheDocument();
});

test('uses home, library and profile as the three top-level destinations', () => {
  render(<MemoryRouter initialEntries={['/']}><AppRoutes /></MemoryRouter>);

  expect(screen.queryByRole('link', { name: /跟练/ })).not.toBeInTheDocument();
  expect(screen.getAllByRole('link')).toHaveLength(3);
  expect(screen.getByRole('link', { name: '我的' })).toHaveAttribute('href', '/profile');
});

test('renders the real profile page', () => {
  render(<MemoryRouter initialEntries={['/profile']}><AppRoutes /></MemoryRouter>);

  expect(screen.getByText('MY BEAUTY PROFILE')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '我的' })).not.toBeInTheDocument();
});
