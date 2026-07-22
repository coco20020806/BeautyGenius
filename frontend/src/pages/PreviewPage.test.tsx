import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PreviewPage } from './PreviewPage';
import { UploadPage } from './UploadPage';

test('shows comparison, makeup summary and suitability decisions', async () => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'task-1' }));
  render(<MemoryRouter><PreviewPage /></MemoryRouter>);

  expect(await screen.findByRole('heading', { name: '适配预览' })).toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole('slider', { name: '妆前妆后对比位置' })).toBeInTheDocument());
  expect(screen.getByRole('button', { name: '适合我' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '需要微调' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '不适合我' })).toBeInTheDocument();
});

test('returns directly to video upload instead of revisiting parsing', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/parsing', '/preview']} initialIndex={1}>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/parsing" element={<h1>解析中</h1>} />
        <Route path="/preview" element={<PreviewPage />} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(screen.getByRole('button', { name: '返回' }));

  expect(screen.getByRole('heading', { name: '上传教程' })).toBeInTheDocument();
});
