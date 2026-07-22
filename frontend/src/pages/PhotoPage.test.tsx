import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, afterEach, expect, test, vi } from 'vitest';
import { HttpError } from '../services/httpClient';
import { PhotoPage } from './PhotoPage';

const uploadPhoto = vi.fn();

vi.mock('../services/makeupService', () => ({
  makeupService: {
    uploadPhoto: (...args: unknown[]) => uploadPhoto(...args),
  },
}));

beforeEach(() => {
  sessionStorage.setItem('makeupTask', JSON.stringify({ taskId: 'demo-task' }));
  uploadPhoto.mockReset();
  uploadPhoto.mockResolvedValue({ photoId: null, previewUrl: null, skipped: true });
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

test('stays on photo page when upload validation rejects', async () => {
  const user = userEvent.setup();
  uploadPhoto.mockRejectedValue(
    new HttpError('照片不符合平视正脸要求（NO_FACE）', 422, 'USER_PHOTO_REJECTED'),
  );
  renderPhotoPage();

  await user.upload(
    screen.getByLabelText('上传本人照片'),
    new File(['face'], 'face.jpg', { type: 'image/jpeg' }),
  );
  await user.click(screen.getByRole('button', { name: '确认上传' }));

  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent('照片不符合平视正脸要求（NO_FACE）');
  });
  expect(screen.queryByRole('heading', { name: '解析中，请稍候…' })).not.toBeInTheDocument();
  expect(screen.getByRole('heading', { name: '确认照片' })).toBeInTheDocument();
});
