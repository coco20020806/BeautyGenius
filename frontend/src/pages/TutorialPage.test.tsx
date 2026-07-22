import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TutorialPage } from './TutorialPage';

test('changes current step and opens eye guide for eye makeup', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/tutorial']}>
      <Routes>
        <Route path="/tutorial" element={<TutorialPage />} />
        <Route path="/eyes" element={<h1>眼部精讲</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(await screen.findByRole('button', { name: '4. 眼影打底' }));
  expect(screen.getByText('裸粉眼影')).toBeInTheDocument();
  await user.click(screen.getByRole('link', { name: '查看眼部精讲' }));

  expect(screen.getByRole('heading', { name: '眼部精讲' })).toBeInTheDocument();
});
