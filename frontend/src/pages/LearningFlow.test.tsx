import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../App';

test('moves from preview through adjustment to tutorial without eye guide', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/preview']}><AppRoutes /></MemoryRouter>);

  await user.click(await screen.findByRole('button', { name: '需要微调' }));
  await user.click(screen.getByRole('button', { name: '生成方案' }));
  await user.click(await screen.findByRole('button', { name: '4. 眼影打底' }));

  expect(await screen.findByRole('heading', { name: '图示教程' })).toBeInTheDocument();
  expect(screen.getByText('裸粉眼影')).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看眼部精讲' })).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /跟练/ })).not.toBeInTheDocument();
});

test('builds an illustrated flow from checked library parts in order', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/library?tab=mix']}><AppRoutes /></MemoryRouter>);

  expect(await screen.findByRole('button', { name: '生成图示流程' })).toBeDisabled();
  await user.click(screen.getByRole('button', { name: '勾选眼妆' }));
  await user.click(screen.getByRole('button', { name: '勾选修容' }));
  await user.click(screen.getByRole('button', { name: '生成图示流程' }));

  expect(await screen.findByRole('heading', { name: '图示教程' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '我的混搭图示流程' })).toBeInTheDocument();
  expect(screen.getByRole('img', { name: '清透玫瑰眼妆 示例图' })).toBeInTheDocument();
  expect(screen.getByText('裸粉眼影')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '2. 柔和轮廓修容' }));
  expect(await screen.findByRole('img', { name: '柔和轮廓修容 示例图' })).toBeInTheDocument();
  expect(screen.getByText('暖棕修容粉')).toBeInTheDocument();
});
