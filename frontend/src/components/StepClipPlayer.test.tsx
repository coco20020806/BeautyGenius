import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { canPlaySourceVideo, canPlayStepClip, StepClipPlayer } from './StepClipPlayer';

describe('canPlayStepClip', () => {
  it('accepts valid url and range', () => {
    expect(canPlayStepClip('https://example.com/v.mp4', { start: 0, end: 3 })).toBe(true);
  });

  it('rejects missing url or inverted range', () => {
    expect(canPlayStepClip(undefined, { start: 0, end: 3 })).toBe(false);
    expect(canPlayStepClip('https://example.com/v.mp4', { start: 5, end: 1 })).toBe(false);
  });
});

describe('canPlaySourceVideo', () => {
  it('accepts any non-empty video url', () => {
    expect(canPlaySourceVideo('https://example.com/v.mp4')).toBe(true);
    expect(canPlaySourceVideo('')).toBe(false);
    expect(canPlaySourceVideo(undefined)).toBe(false);
  });
});

describe('StepClipPlayer', () => {
  beforeEach(() => {
    Object.defineProperty(HTMLMediaElement.prototype, 'play', {
      configurable: true,
      value: vi.fn().mockResolvedValue(undefined),
    });
    Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
      configurable: true,
      value: vi.fn(),
    });
  });

  it('renders dialog and closes on button click', () => {
    const onClose = vi.fn();
    render(
      <StepClipPlayer
        open
        videoUrl="https://example.com/v.mp4"
        clip={{ start: 1, end: 4 }}
        title="步骤 1 · 腮红"
        onClose={onClose}
      />,
    );

    expect(screen.getByRole('dialog', { name: '步骤视频：步骤 1 · 腮红' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '关闭视频' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('plays the full original video when clip is omitted', () => {
    render(
      <StepClipPlayer open videoUrl="https://example.com/v.mp4" title="完整原视频" onClose={() => undefined} />,
    );
    expect(screen.getByRole('dialog', { name: '步骤视频：完整原视频' })).toBeInTheDocument();
    expect(document.querySelector('video')?.getAttribute('src')).toBe('https://example.com/v.mp4');
  });

  it('pauses when playback reaches clip end', () => {
    render(
      <StepClipPlayer
        open
        videoUrl="https://example.com/v.mp4"
        clip={{ start: 1, end: 4 }}
        onClose={() => undefined}
      />,
    );

    const video = document.querySelector('video');
    expect(video).toBeTruthy();
    Object.defineProperty(video!, 'currentTime', {
      configurable: true,
      writable: true,
      value: 4.2,
    });
    fireEvent(video!, new Event('timeupdate'));
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
  });
});
