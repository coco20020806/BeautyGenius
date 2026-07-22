import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CollectedTutorialPage } from './CollectedTutorialPage';
import { LibraryPage } from './LibraryPage';

test('renders preview practice steps and illustrated sections for sample 1', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/library/collected/collected-sample-1']}>
      <Routes>
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/library/collected/:assetId" element={<CollectedTutorialPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '早八五分钟妆' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '妆容预览' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '跟练步骤' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '图示教程' })).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: '解析 JSON' })).not.toBeInTheDocument();
  expect(screen.getByLabelText('教程步骤')).toBeInTheDocument();
  expect(screen.getAllByText('产品').length).toBeGreaterThan(0);
  expect(screen.getAllByText('手法').length).toBeGreaterThan(0);
  expect(screen.getByText('珂岸面部素颜霜')).toBeInTheDocument();
  expect(screen.getByAltText('妆前 示例图')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /查看原视频切片/ })).toBeEnabled();
  const playButtons = screen.getAllByRole('button', { name: '看视频' });
  expect(playButtons.length).toBeGreaterThan(0);
  expect(playButtons.every((button) => !(button as HTMLButtonElement).disabled)).toBe(true);
  expect(screen.queryByRole('button', { name: /查看眼部精讲/ })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: /查看原视频切片/ }));
  expect(screen.getByRole('dialog', { name: /步骤视频/ })).toBeInTheDocument();
  expect(document.querySelector('video')?.getAttribute('src')).toBe('/fixtures/collected/sample-1.mp4');
  await user.click(screen.getByRole('button', { name: '关闭视频' }));
  expect(screen.queryByRole('dialog', { name: /步骤视频/ })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '返回' }));
  expect(await screen.findByRole('tab', { name: '收藏教程' })).toBeInTheDocument();
});

test('redirects unknown collected ids back to the library', async () => {
  render(
    <MemoryRouter initialEntries={['/library/collected/missing-id']}>
      <Routes>
        <Route path="/library" element={<h1>知识库首页</h1>} />
        <Route path="/library/collected/:assetId" element={<CollectedTutorialPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '知识库首页' })).toBeInTheDocument();
});
