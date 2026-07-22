import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../App';

test('moves from preview through adjustment to tutorial and eye guide', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/preview']}><AppRoutes /></MemoryRouter>);

  await user.click(await screen.findByRole('button', { name: '需要微调' }));
  await user.click(screen.getByRole('button', { name: '生成方案' }));
  await user.click(await screen.findByRole('button', { name: '4. 眼影打底' }));
  await user.click(screen.getByRole('link', { name: '查看眼部精讲' }));

  expect(screen.getByRole('heading', { name: '眼部精讲' })).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /跟练/ })).not.toBeInTheDocument();
});

test('loads a preset preview and tutorial with untouched parts skipped', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/library?tab=mix']}><AppRoutes /></MemoryRouter>);

  expect(screen.getByRole('button', { name: '生成效果' })).toBeEnabled();
  await user.click(screen.getByRole('button', { name: '生成效果' }));

  expect(await screen.findByRole('heading', { name: '生成妆效中' })).toBeInTheDocument();
  expect(await screen.findByRole('heading', { name: '混搭效果预览' }, { timeout: 3000 })).toBeInTheDocument();
  await user.click(await screen.findByRole('button', { name: '适合我' }));
  expect(await screen.findByRole('heading', { name: '图示教程' })).toBeInTheDocument();
});
