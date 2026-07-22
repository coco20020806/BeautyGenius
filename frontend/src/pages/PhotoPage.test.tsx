import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi } from 'vitest';
import { PhotoPage } from './PhotoPage';

beforeEach(() => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'demo-task' }));
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:photo-preview');
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
});

afterEach(() => vi.restoreAllMocks());

function renderPhotoPage() {
  return render(
    <MemoryRouter initialEntries={['/photo']}>
      <Routes>
        <Route path="/photo" element={<PhotoPage />} />
        <Route path="/parsing" element={<h1>解析中，请稍候…</h1>} />
      </Routes>
    </MemoryRouter>,
  );
}

test('allows the user to skip a personal photo', async () => {
  const user = userEvent.setup();
  renderPhotoPage();

  expect(screen.getByText('推荐先跳过，使用默认示意脸即可继续生成教程图示')).toBeInTheDocument();
  expect(screen.getByText('上传正面照片')).toBeInTheDocument();
  expect(screen.getByText('也可以点击上方人像上传本人照片，效果会更贴近你')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '暂时跳过（使用标准人脸生成）' }));

  await waitFor(() => {
    expect(screen.getByRole('heading', { name: '解析中，请稍候…' })).toBeInTheDocument();
  });
});

test('previews a selected image before confirmation', async () => {
  const user = userEvent.setup();
  renderPhotoPage();

  await user.upload(
    screen.getByLabelText('上传本人照片'),
    new File(['face'], 'face.jpg', { type: 'image/jpeg' }),
  );

  expect(screen.getByRole('img', { name: '待确认的本人照片' })).toHaveAttribute('src', 'blob:photo-preview');
});
