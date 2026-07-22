import faceBefore from '../assets/face-before.svg';
import type { MakeupPart } from '../types/learning';

interface FaceLayersProps {
  activePart: MakeupPart;
  color: string;
}

export function FaceLayers({ activePart, color }: FaceLayersProps) {
  return (
    <div className="face-layers" aria-label={`当前高亮：${activePart}`}>
      <img src={faceBefore} alt="图示教程脸部底图" />
      <svg viewBox="0 0 640 680" aria-hidden="true">
        <g className={activePart === 'base' ? 'is-active' : ''} fill={color}><ellipse cx="320" cy="365" rx="126" ry="152" opacity=".16" /></g>
        <g className={activePart === 'brows' ? 'is-active' : ''} stroke={color} strokeWidth="16" strokeLinecap="round" opacity=".55"><path d="M225 291C251 275 276 276 301 291"/><path d="M339 291C366 276 391 275 416 291"/></g>
        <g className={activePart === 'eyes' ? 'is-active' : ''} fill={color} opacity=".52"><ellipse cx="266" cy="313" rx="47" ry="25"/><ellipse cx="375" cy="313" rx="47" ry="25"/></g>
        <g className={activePart === 'blush' ? 'is-active' : ''} fill={color} opacity=".42"><ellipse cx="247" cy="382" rx="65" ry="33" transform="rotate(-8 247 382)"/><ellipse cx="393" cy="382" rx="65" ry="33" transform="rotate(8 393 382)"/></g>
        <g className={activePart === 'contour' ? 'is-active' : ''} fill={color} opacity=".28"><path d="M206 329C194 402 220 464 265 504C226 487 191 440 184 381C180 352 188 326 206 329Z"/><path d="M434 504C479 464 505 402 493 329C511 326 519 352 515 381C508 440 473 487 434 504Z"/></g>
        <g className={activePart === 'highlight' ? 'is-active' : ''} fill={color} opacity=".68"><path d="M314 322H326L332 402H307L314 322Z"/><ellipse cx="320" cy="276" rx="28" ry="12"/></g>
        <g className={activePart === 'lips' ? 'is-active' : ''} fill={color} opacity=".84"><path d="M278 424C304 402 337 402 363 424C338 452 302 452 278 424Z"/></g>
      </svg>
    </div>
  );
}
