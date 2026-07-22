import { ChevronsLeftRight } from 'lucide-react';
import { useRef, useState } from 'react';

interface BeforeAfterSliderProps {
  beforeSrc: string;
  afterSrc: string;
  frameAspectRatio?: number;
  objectPosition?: string;
  /** 妆后层透明度（浓淡色块控制）；默认 1 */
  afterOpacity?: number;
}

export function BeforeAfterSlider({
  beforeSrc,
  afterSrc,
  frameAspectRatio,
  objectPosition = '50% 50%',
  afterOpacity = 1,
}: BeforeAfterSliderProps) {
  const [position, setPosition] = useState(50);
  const frameRef = useRef<HTMLDivElement>(null);

  function updateFromClientX(clientX: number) {
    const bounds = frameRef.current?.getBoundingClientRect();
    if (!bounds?.width) return;
    setPosition(Math.round(Math.min(100, Math.max(0, ((clientX - bounds.left) / bounds.width) * 100))));
  }

  const imageStyle = { objectPosition } as const;
  const frameStyle =
    frameAspectRatio && frameAspectRatio > 0
      ? ({ aspectRatio: frameAspectRatio, height: 'auto' } as const)
      : undefined;
  const clampedOpacity = Math.min(1, Math.max(0, afterOpacity));

  return (
    <section className="comparison" aria-label="妆前妆后效果对比">
      <div
        ref={frameRef}
        className={
          frameAspectRatio && frameAspectRatio > 0
            ? 'comparison__frame comparison__frame--sized'
            : 'comparison__frame'
        }
        style={frameStyle}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture?.(event.pointerId);
          updateFromClientX(event.clientX);
        }}
        onPointerMove={(event) => {
          if (event.currentTarget.hasPointerCapture?.(event.pointerId)) updateFromClientX(event.clientX);
        }}
      >
        <img
          className="comparison__image comparison__image--before"
          src={beforeSrc}
          alt="原始状态"
          draggable={false}
          style={imageStyle}
        />
        <div
          className="comparison__after"
          style={{ clipPath: `inset(0 0 0 ${position}%)`, opacity: clampedOpacity }}
        >
          <img className="comparison__image" src={afterSrc} alt="化妆后效果" draggable={false} style={imageStyle} />
        </div>
        <span className="comparison__label comparison__label--before">原始状态</span>
        <span className="comparison__label comparison__label--after">化妆后</span>
        <span className="comparison__divider" style={{ left: `${position}%` }} aria-hidden="true">
          <span><ChevronsLeftRight size={19} /></span>
        </span>
        <input
          className="comparison__range"
          type="range"
          min="0"
          max="100"
          step="5"
          value={position}
          aria-label="妆前妆后对比位置"
          onChange={(event) => setPosition(Number(event.target.value))}
          onKeyDown={(event) => {
            if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
              event.preventDefault();
              setPosition((value) => Math.min(100, value + 5));
            } else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
              event.preventDefault();
              setPosition((value) => Math.max(0, value - 5));
            } else if (event.key === 'Home') {
              event.preventDefault();
              setPosition(0);
            } else if (event.key === 'End') {
              event.preventDefault();
              setPosition(100);
            }
          }}
        />
      </div>
      <div className="comparison__actions">
        <button type="button" onClick={() => setPosition(0)}>看原图</button>
        <span>拖动查看完整效果</span>
        <button type="button" onClick={() => setPosition(100)}>看妆后</button>
      </div>
    </section>
  );
}
