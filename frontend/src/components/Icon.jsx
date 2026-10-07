const PATHS = {
  target: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" /></>,
  layers: <><path d="m12 3 9 4.5-9 4.5-9-4.5z" /><path d="m3 12 9 4.5 9-4.5" /><path d="m3 16.5 9 4.5 9-4.5" /></>,
  palette: <><circle cx="13.5" cy="6.5" r="1.3" /><circle cx="17.5" cy="10.5" r="1.3" /><circle cx="8.5" cy="7.5" r="1.3" /><circle cx="6.5" cy="12.5" r="1.3" /><path d="M12 2.5a9.5 9.5 0 0 0 0 19c.9 0 1.5-.7 1.5-1.5 0-.4-.2-.8-.4-1-.3-.3-.4-.7-.4-1.1 0-.9.7-1.5 1.5-1.5H16a5.5 5.5 0 0 0 5.5-5.5c0-4.6-4.3-8.4-9.5-8.4z" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20.5 20.5-4.5-4.5" /></>,
  pen: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" /></>,
  shield: <><path d="M12 21.5s8-3.8 8-9.8V5.2L12 2.5 4 5.2v6.5c0 6 8 9.8 8 9.8z" /><path d="m8.8 12 2.2 2.2 4.2-4.4" /></>,
  file: <><path d="M14.5 2.5H6.5a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7.5z" /><path d="M14 2.5v5.5h5.5" /><path d="M8.5 13h7M8.5 17h5" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  upload: <><path d="M20.5 15v3.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2V15" /><path d="m16.5 8-4.5-4.5L7.5 8" /><path d="M12 3.5v12" /></>,
  download: <><path d="M20.5 15v3.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2V15" /><path d="m7.5 10.5 4.5 4.5 4.5-4.5" /><path d="M12 15V3.5" /></>,
  play: <path d="M7 4.5v15l12.5-7.5z" />,
  check: <path d="M20 6.5 9.5 17 4 11.5" />,
  x: <path d="M18 6 6 18M6 6l12 12" />,
  spark: <path d="M12 2.5c.6 4.8 2.7 6.9 7.5 7.5-4.8.6-6.9 2.7-7.5 7.5-.6-4.8-2.7-6.9-7.5-7.5 4.8-.6 6.9-2.7 7.5-7.5zM19 16c.3 2 1 2.7 3 3-2 .3-2.7 1-3 3-.3-2-1-2.7-3-3 2-.3 2.7-1 3-3z" />,
  terminal: <><rect x="2.5" y="4" width="19" height="16" rx="2.5" /><path d="m7 9.5 3 2.5-3 2.5M12.5 15h4.5" /></>,
  trash: <><path d="M4 6.5h16" /><path d="M18 6.5V19a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6.5" /><path d="M9 6.5V4.5a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 4.5v2" /></>,
  eye: <><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>,
  refresh: <><path d="M20.5 12a8.5 8.5 0 1 1-2.6-6.1L20.5 8.5" /><path d="M20.5 3.5v5h-5" /></>,
  alert: <><circle cx="12" cy="12" r="9.5" /><path d="M12 7.5v5.5M12 16.5h.01" /></>,
  folder: <path d="M3 7.5V18a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9.5a2 2 0 0 0-2-2h-7l-2-3H5a2 2 0 0 0-2 2z" />,
  bolt: <path d="M13 2.5 4 14h7.5l-1 7.5L20 10h-7.5z" />,
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" /></>,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  type: <><path d="M4 7V5h16v2" /><path d="M12 5v14M9 19h6" /></>,
  'chevron-left': <path d="m15 18-6-6 6-6" />,
  'chevron-right': <path d="m9 18 6-6-6-6" />,
  grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /></>,
  maximize: <><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" /></>,
  minimize: <><path d="M4 14h6m0 0v6m0-6-7 7m17-11h-6m0 0V4m0 6 7-7" /></>,
}

export default function Icon({ name, size = 18, strokeWidth = 1.8, className, style }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round"
      className={className} style={style} aria-hidden="true" focusable="false">
      {PATHS[name]}
    </svg>
  )
}
