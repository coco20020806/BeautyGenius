import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TutorialPage } from './TutorialPage';

test('changes current step for eye makeup without eye guide', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/tutorial']}>
      <Routes>
        <Route path="/tutorial" element={<TutorialPage />} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(await screen.findByRole('button', { name: '4. 眼影打底' }));
  expect(screen.getByText('裸粉眼影')).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: '查看眼部精讲' })).not.toBeInTheDocument();
});

test('shows the diagram by default and opens the source video from the slice button', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter
      initialEntries={[{ pathname: '/tutorial', state: { tutorialId: 'preset-eyes-rose', from: '/library?tab=part' } }]}
    >
      <Routes>
        <Route path="/tutorial" element={<TutorialPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole('heading', { name: '图示教程' })).toBeInTheDocument();
  expect(screen.getByAltText('清透玫瑰眼妆 示例图')).toBeInTheDocument();
  expect(document.querySelector('video')).not.toBeInTheDocument();

  const sliceButton = screen.getByRole('button', { name: /查看原视频切片/ });
  expect(sliceButton).toBeEnabled();
  await user.click(sliceButton);

  expect(screen.getByRole('dialog', { name: /步骤视频/ })).toBeInTheDocument();
  expect(document.querySelector('video')?.getAttribute('src')).toMatch(/eyes\/media\/source\.mp4/);

  await user.click(screen.getByRole('button', { name: '关闭视频' }));
  expect(screen.queryByRole('dialog', { name: /步骤视频/ })).not.toBeInTheDocument();
  expect(screen.getByAltText('清透玫瑰眼妆 示例图')).toBeInTheDocument();
});
