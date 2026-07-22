import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { LibraryPage } from './LibraryPage';

function TutorialTarget() {
  const location = useLocation();
  const state = location.state as { tutorialId?: string } | null;
  return <h1>图示教程 <span>{state?.tutorialId}</span></h1>;
}

test('filters assets and sends a selected part to mix editor', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/library']}>
      <Routes>
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/tutorial" element={<TutorialTarget />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.queryByRole('searchbox')).not.toBeInTheDocument();
  const tabRow = screen.getByRole('group', { name: '知识库分类与筛选' });
  expect(within(tabRow).getByRole('tab', { name: '教程' })).toBeInTheDocument();
  expect(within(tabRow).getByRole('button', { name: '筛选' })).toBeInTheDocument();
  await user.click(await screen.findByRole('tab', { name: '部位' }));
  const partFilters = screen.getByLabelText('部位筛选');
  for (const part of ['全部', '底妆', '眼妆', '腮红', '修容', '唇妆']) expect(within(partFilters).getByRole('button', { name: part })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '眉毛' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '高光' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '清透' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '教程资产' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '部位资产' })).not.toBeInTheDocument();
  expect((await screen.findAllByRole('button', { name: /眼妆|修容|唇/ })).filter((button) => button.closest('.asset-card'))).toHaveLength(3);
  await user.click(screen.getByRole('button', { name: '眼妆' }));
  expect(await screen.findByRole('img', { name: '清透玫瑰眼妆视频封面' })).toBeInTheDocument();
  expect(document.querySelectorAll('.asset-card')).toHaveLength(1);
  expect(document.querySelector('input[type="file"]')).not.toBeInTheDocument();
  expect(document.querySelector('video')).not.toBeInTheDocument();
  await user.click(await screen.findByRole('button', { name: /清透玫瑰眼妆/ }));

  expect(screen.getByRole('heading', { name: /图示教程/ })).toHaveTextContent('preset-eyes-rose');
});

test('replaces the product tab with the embedded mix editor', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={['/library']}><LibraryPage /></MemoryRouter>);

  expect(screen.queryByRole('heading', { name: '知识库' })).not.toBeInTheDocument();
  expect(document.querySelector('.library-mark')).not.toBeInTheDocument();
  expect(screen.queryByRole('tab', { name: '产品' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('tab', { name: '混搭' }));

  expect(screen.getByRole('region', { name: '混搭编辑' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '展开底妆选项' })).toHaveAttribute('aria-expanded', 'false');
  expect(screen.getByRole('button', { name: '生成效果' })).toBeEnabled();
  expect(screen.queryByRole('img', { name: '混搭妆容预览' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '筛选' })).not.toBeInTheDocument();
});
