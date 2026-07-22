import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';

export interface VideoClipRange {
  start: number;
  end: number;
}

interface StepClipPlayerProps {
  open: boolean;
  videoUrl: string;
  /** When omitted or invalid, the full original video plays. */
  clip?: VideoClipRange | null;
  title?: string;
  onClose: () => void;
}

function isValidClip(clip: VideoClipRange): boolean {
  return (
    Number.isFinite(clip.start) &&
    Number.isFinite(clip.end) &&
    clip.end > clip.start &&
    clip.start >= 0
  );
}

export function StepClipPlayer({ open, videoUrl, clip, title, onClose }: StepClipPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const limitedClip = clip && isValidClip(clip) ? clip : null;

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    const video = videoRef.current;
    if (!open || !video) return;

    let cancelled = false;

    const seekAndPlay = () => {
      if (cancelled) return;
      if (limitedClip) {
        try {
          video.currentTime = limitedClip.start;
        } catch {
          /* ignore seek errors before ready */
        }
      }
      void video.play().catch(() => {
        /* autoplay may be blocked; controls remain available */
      });
    };

    const onTimeUpdate = () => {
      if (!limitedClip) return;
      if (video.currentTime >= limitedClip.end) {
        video.pause();
        try {
          video.currentTime = limitedClip.end;
        } catch {
          /* ignore */
        }
      }
    };

    const onLoadedMetadata = () => {
      seekAndPlay();
    };

    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('loadedmetadata', onLoadedMetadata);

    if (video.readyState >= 1) {
      seekAndPlay();
    }

    return () => {
      cancelled = true;
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('loadedmetadata', onLoadedMetadata);
      video.pause();
    };
  }, [open, videoUrl, limitedClip?.start, limitedClip?.end]);

  if (!open) return null;

  return (
    <div
      className="step-clip-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={title ? `步骤视频：${title}` : '步骤视频'}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="step-clip-panel">
        <header className="step-clip-panel__header">
          <h2>{title || '步骤视频'}</h2>
          <button className="icon-button" type="button" aria-label="关闭视频" onClick={onClose}>
            <X size={20} />
          </button>
        </header>
        <video
          ref={videoRef}
          className="step-clip-panel__video"
          src={videoUrl}
          controls
          playsInline
          preload="metadata"
        />
      </div>
    </div>
  );
}

export function canPlayStepClip(
  videoUrl: string | null | undefined,
  clip: VideoClipRange | null | undefined,
): boolean {
  return Boolean(videoUrl && clip && isValidClip(clip));
}

/** Full original video is playable whenever a source URL exists. */
export function canPlaySourceVideo(videoUrl: string | null | undefined): boolean {
  return Boolean(videoUrl);
}
