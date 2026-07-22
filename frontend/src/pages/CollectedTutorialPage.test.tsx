import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CollectedTutorialPage } from './CollectedTutorialPage';
import { LibraryPage } from './LibraryPage';

test('renders preview json and illustrated placeholder sections', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/library/collected/collected-sample-1']}>
      <Routes>
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/library/collected/:assetId" element={<CollectedTutorialPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '示例视频1' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '妆容预览' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '解析 JSON' })).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '图示教程' })).toBeInTheDocument();
  expect(screen.getByLabelText('tutorial.json 占位')).toHaveTextContent('placeholder_sample_1');
  expect(screen.getByLabelText('tutorial.json 占位')).toHaveTextContent('示例结构 · 待接入真实解析');
  expect(screen.getByRole('button', { name: /查看原视频切片/ })).toBeDisabled();
  expect(screen.getByRole('button', { name: /查看眼部精讲/ })).toBeDisabled();

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
