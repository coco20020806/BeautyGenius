interface EyeDiagramProps {
  activeRegion: string;
  color: string;
}

export function EyeDiagram({ activeRegion, color }: EyeDiagramProps) {
  return (
    <svg className="eye-diagram" viewBox="0 0 700 390" role="img" aria-label="可交互眼部图示">
      <defs><linearGradient id="skin" x2="0" y2="1"><stop stopColor="#f5d9ca"/><stop offset="1" stopColor="#ecc5b5"/></linearGradient></defs>
      <rect width="700" height="390" rx="28" fill="url(#skin)"/>
      <path d="M95 125C208 52 469 50 596 126" stroke="#4a3530" strokeWidth="28" strokeLinecap="round" opacity=".82"/>
      <path d="M113 242C198 132 463 121 585 234C463 320 230 331 113 242Z" fill="#fffaf7" stroke="#6f4b43" strokeWidth="9"/>
      <ellipse cx="358" cy="236" rx="91" ry="86" fill="#a98265"/><ellipse cx="358" cy="236" rx="52" ry="52" fill="#382b28"/><circle cx="380" cy="210" r="15" fill="white" opacity=".9"/>
      <path d="M113 240C206 164 464 148 585 232" stroke="#352826" strokeWidth="15" strokeLinecap="round"/>
      <path d="M119 238C215 320 469 320 584 234" stroke="#9a685e" strokeWidth="5" opacity=".55"/>
      {activeRegion === 'shadow' && <path d="M135 213C221 107 482 107 564 211C446 168 241 168 135 213Z" fill={color} opacity=".58"/>}
      {activeRegion === 'liner' && <path d="M114 241C223 152 484 159 586 232L642 211" fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"/>}
      {activeRegion === 'aegyo' && <path d="M172 293C272 332 434 333 528 286" fill="none" stroke={color} strokeWidth="18" strokeLinecap="round" opacity=".7"/>}
      {activeRegion === 'lashes' && <g stroke={color} strokeWidth="7" strokeLinecap="round"><path d="M178 199L156 164"/><path d="M229 177L217 135"/><path d="M286 163L281 119"/><path d="M424 161L433 117"/><path d="M483 174L501 132"/><path d="M536 198L562 158"/></g>}
      {activeRegion === 'inner' && <circle cx="119" cy="242" r="32" fill={color} opacity=".78"/>}
      {activeRegion === 'lower' && <path d="M478 290C523 278 559 257 590 230" stroke={color} strokeWidth="15" strokeLinecap="round" opacity=".72"/>}
      {activeRegion === 'distance' && <path d="M151 117C257 67 476 69 553 120" stroke={color} strokeWidth="40" strokeLinecap="round" opacity=".26"/>}
      <path d="M128 240C211 151 465 143 590 232" fill="none" stroke="#bd5962" strokeWidth="3" strokeDasharray="9 9" opacity=".75"/>
    </svg>
  );
}
