import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { makeupService } from '../services/makeupService';
import { UploadPage } from './UploadPage';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('UploadPage', () => {
  it('shows selected video and enables continue', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    );
    const file = new File(['video'], 'daily-look.mp4', { type: 'video/mp4' });

    await user.upload(screen.getByLabelText('选择教程视频'), file);

    expect(screen.getByText('daily-look.mp4')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '下一步' })).toBeEnabled();
    expect(screen.getByRole('navigation', { name: '主导航' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /快速解析/ })).toBeChecked();
  });

  it('passes fastParse=false when unchecked', async () => {
    const uploadSpy = vi.spyOn(makeupService, 'uploadVideo').mockResolvedValue({
      taskId: 'task-test',
      fileName: 'daily-look.mp4',
      fileSize: 100,
      status: 'uploaded',
      parseMode: 'full',
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    );
    const file = new File(['video'], 'daily-look.mp4', { type: 'video/mp4' });
    await user.upload(screen.getByLabelText('选择教程视频'), file);
    await user.click(screen.getByRole('checkbox', { name: /快速解析/ }));
    await user.click(screen.getByRole('button', { name: '下一步' }));

    expect(uploadSpy).toHaveBeenCalledWith(file, { fastParse: false, skipMakeupPreview: false });
  });

  it('passes skipMakeupPreview=true when checked', async () => {
    const uploadSpy = vi.spyOn(makeupService, 'uploadVideo').mockResolvedValue({
      taskId: 'task-test',
      fileName: 'daily-look.mp4',
      fileSize: 100,
      status: 'uploaded',
      skipMakeupPreview: true,
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>,
    );
    const file = new File(['video'], 'daily-look.mp4', { type: 'video/mp4' });
    await user.upload(screen.getByLabelText('选择教程视频'), file);
    expect(screen.getByRole('checkbox', { name: '跳过妆容预览' })).not.toBeChecked();
    await user.click(screen.getByRole('checkbox', { name: '跳过妆容预览' }));
    await user.click(screen.getByRole('button', { name: '下一步' }));

    expect(uploadSpy).toHaveBeenCalledWith(file, { fastParse: true, skipMakeupPreview: true });
  });

  it('skips photo and parsing via dev shortcut', async () => {
    const skipSpy = vi.spyOn(makeupService, 'skipToDevPreview').mockResolvedValue({
      taskId: 'task-dev-skip',
      status: 'completed',
    });
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/preview" element={<h1>适配预览</h1>} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: '跳过前两步（开发）' }));

    expect(skipSpy).toHaveBeenCalled();
    expect(JSON.parse(sessionStorage.getItem('makeupTask') ?? '{}').taskId).toBe('task-dev-skip');
    expect(await screen.findByRole('heading', { name: '适配预览' })).toBeInTheDocument();
  });
});
