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
  await user.click(await screen.findByRole('button', { name: '暂时跳过' }));

  await waitFor(() => expect(screen.getByRole('heading', { name: '适配预览' })).toBeInTheDocument());
  expect(await screen.findByRole('slider', { name: '妆前妆后对比位置' })).toBeInTheDocument();
});

test('keeps bottom navigation on top-level destinations', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/']}><AppRoutes /></MemoryRouter>);

  await user.click(screen.getByRole('link', { name: /知识库/ }));

  expect(screen.getByRole('heading', { name: '知识库' })).toBeInTheDocument();
  expect(screen.getByRole('navigation', { name: '主导航' })).toBeInTheDocument();
});
