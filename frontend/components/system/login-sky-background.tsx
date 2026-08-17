export function LoginSkyBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 bg-[linear-gradient(180deg,#8ec8ea_0%,#c5e4f6_38%,#eaf4fb_72%,#f7f3ee_100%)]" />
      <div className="absolute -top-24 -left-16 h-72 w-72 rounded-full bg-[radial-gradient(circle,rgba(255,236,179,0.85)_0%,rgba(255,236,179,0)_70%)]" />
      <div className="absolute inset-y-0 right-0 w-1/3 bg-[linear-gradient(180deg,rgba(121,17,62,0.07),transparent_55%)]" />

      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
        <path
          d="M-40 620 C 220 540, 480 700, 760 610 S 1220 520, 1480 600"
          fill="none"
          stroke="rgba(38,55,70,0.08)"
          strokeDasharray="8 14"
          strokeWidth="1.5"
        />
        <g className="animate-login-cloud-slow" opacity="0.55">
          <Cloud x={80} y={120} scale={1.15} />
          <Cloud x={980} y={70} scale={0.9} />
        </g>
        <g className="animate-login-cloud-fast" opacity="0.4">
          <Cloud x={420} y={210} scale={0.75} />
          <Cloud x={1180} y={250} scale={1.05} />
          <Cloud x={-40} y={340} scale={0.65} />
        </g>
      </svg>

      <div className="animate-login-uav absolute left-0 top-0">
        <FixedWingWithBanner />
      </div>
    </div>
  );
}

function Cloud({ x, y, scale }: { x: number; y: number; scale: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <ellipse cx="70" cy="28" rx="70" ry="22" fill="white" />
      <ellipse cx="28" cy="24" rx="32" ry="18" fill="white" />
      <ellipse cx="108" cy="22" rx="36" ry="20" fill="white" />
      <ellipse cx="64" cy="14" rx="28" ry="16" fill="white" />
    </g>
  );
}

function FixedWingWithBanner() {
  return (
    <svg
      width="620"
      height="150"
      viewBox="0 0 620 150"
      className="drop-shadow-[0_12px_20px_rgba(38,55,70,0.22)]"
    >
      <defs>
        <linearGradient id="uav-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#eef2f5" />
          <stop offset="42%" stopColor="#c5ced6" />
          <stop offset="100%" stopColor="#7d8893" />
        </linearGradient>
        <linearGradient id="uav-wing" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f4f7f9" />
          <stop offset="55%" stopColor="#b7c1ca" />
          <stop offset="100%" stopColor="#6f7b86" />
        </linearGradient>
        <linearGradient id="uav-tail" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#dce3e9" />
          <stop offset="100%" stopColor="#5f6b75" />
        </linearGradient>
        <radialGradient id="uav-prop" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#9aa6b0" stopOpacity="0.15" />
          <stop offset="55%" stopColor="#6b7680" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#3d4852" stopOpacity="0.08" />
        </radialGradient>
        <radialGradient id="uav-glass" cx="35%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#d9e7f2" />
          <stop offset="55%" stopColor="#4d5e6c" />
          <stop offset="100%" stopColor="#1f2933" />
        </radialGradient>
      </defs>

      <g fill="none">
        <path
          d="M228 72 C 252 64, 276 62, 298 68"
          stroke="#4a5560"
          strokeOpacity="0.45"
          strokeWidth="1.6"
          strokeDasharray="5 6"
        />
        <path
          d="M14 42 C 28 30, 44 32, 56 42 L 216 46 C 224 46, 230 52, 230 58 L 230 84 C 230 90, 224 96, 216 96 L 56 92 C 44 102, 28 100, 14 88 Z"
          fill="rgba(255,255,255,0.94)"
          stroke="#79113e"
          strokeOpacity="0.55"
          strokeWidth="1.4"
        />
        <path d="M56 42 L 56 92" stroke="#79113e" strokeOpacity="0.22" strokeWidth="1" />
        <path d="M98 43.5 L 98 91" stroke="#79113e" strokeOpacity="0.22" strokeWidth="1" />
        <path d="M140 45 L 140 90" stroke="#79113e" strokeOpacity="0.22" strokeWidth="1" />
        <path d="M182 46 L 182 89" stroke="#79113e" strokeOpacity="0.22" strokeWidth="1" />
        <text
          x="122"
          y="74"
          textAnchor="middle"
          fill="#79113e"
          fontFamily="var(--font-sans), ui-sans-serif, system-ui, sans-serif"
          fontSize="15"
          fontWeight="600"
          letterSpacing="0.02em"
        >
          İstikbal Göklerdedir.
        </text>
      </g>

      <g>
        <ellipse cx="430" cy="92" rx="78" ry="8" fill="#263746" fillOpacity="0.12" />

        <path
          d="M418 78 L 458 118 C 462 124, 472 122, 474 116 L 438 78 Z"
          fill="url(#uav-wing)"
          stroke="#5c6770"
          strokeWidth="0.8"
        />
        <path
          d="M424 62 L 478 10 C 482 5, 494 7, 496 14 L 452 64 Z"
          fill="url(#uav-wing)"
          stroke="#5c6770"
          strokeWidth="0.9"
        />

        <path
          d="M318 68 C 328 62, 360 58, 402 56 C 448 54, 500 52, 538 60 C 552 63, 556 70, 546 74 C 528 80, 500 82, 470 80 C 430 78, 380 76, 344 74 C 328 73, 318 72, 318 68 Z"
          fill="url(#uav-body)"
          stroke="#5a6570"
          strokeWidth="0.9"
        />
        <path
          d="M402 58 C 430 50, 468 48, 498 54"
          fill="none"
          stroke="#ffffff"
          strokeOpacity="0.45"
          strokeWidth="1.4"
        />
        <path d="M390 64 L 500 66" fill="none" stroke="#4a5560" strokeOpacity="0.18" strokeWidth="0.8" />
        <rect x="456" y="58" width="18" height="6" rx="1.5" fill="#4b5560" fillOpacity="0.35" />

        <path
          d="M332 66 L 356 22 C 358 16, 368 16, 372 22 L 352 66 Z"
          fill="url(#uav-tail)"
          stroke="#5c6770"
          strokeWidth="0.8"
        />
        <path
          d="M334 72 L 352 102 C 354 108, 364 108, 366 102 L 348 72 Z"
          fill="url(#uav-tail)"
          stroke="#5c6770"
          strokeWidth="0.8"
        />

        <ellipse cx="308" cy="70" rx="7" ry="26" fill="url(#uav-prop)" stroke="#6b7680" strokeOpacity="0.25" />
        <circle cx="308" cy="70" r="4.2" fill="#4b5560" />
        <circle cx="308" cy="70" r="1.7" fill="#d7dde2" />

        <circle cx="528" cy="84" r="9" fill="url(#uav-glass)" stroke="#3d4852" strokeWidth="1" />
        <circle cx="525" cy="81" r="2.2" fill="#ffffff" fillOpacity="0.55" />
        <path d="M528 75 L 528 67" stroke="#6b7680" strokeWidth="1.4" />
      </g>
    </svg>
  );
}
