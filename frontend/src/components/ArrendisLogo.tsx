
interface ArrendisLogoProps {
  size?: 'sm' | 'md' | 'lg';
  layout?: 'horizontal' | 'vertical';
  showSubtitle?: boolean;
  color?: string;
  className?: string;
}

export default function ArrendisLogo({
  size = 'sm',
  layout = 'horizontal',
  showSubtitle,
  color,
  className = '',
}: ArrendisLogoProps) {
  // Determine sizes
  const markSize = size === 'lg' ? 38 : size === 'md' ? 30 : 22;
  const shouldShowSubtitle = showSubtitle !== undefined ? showSubtitle : size !== 'sm';

  const markColor = color || 'var(--brand-burgundy, #6b0008)';
  const textColor = 'var(--text-primary, #1c1917)';

  return (
    <div
      className={`arrendis-brand-lockup arrendis-brand-lockup--${size} arrendis-brand-lockup--${layout} ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: layout === 'vertical' ? 'center' : 'center',
        flexDirection: layout === 'vertical' ? 'column' : 'row',
        gap: size === 'lg' ? '0.85rem' : size === 'md' ? '0.65rem' : '0.55rem',
        textDecoration: 'none',
        lineHeight: 1,
      }}
    >
      {/* Architectural Keystone Portal Emblem */}
      <svg
        width={markSize}
        height={markSize}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0, color: markColor }}
        aria-hidden="true"
      >
        {/* Foundation line */}
        <line x1="3" y1="28" x2="29" y2="28" stroke="currentColor" strokeWidth="1.75" strokeLinecap="square" />
        
        {/* Outer monumental portal arch */}
        <path
          d="M6 28V14C6 8.477 10.477 4 16 4C21.523 4 26 8.477 26 14V28"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="square"
        />

        {/* Inner masonry recess */}
        <path
          d="M10.5 28V15C10.5 11.962 12.962 9.5 16 9.5C19.038 9.5 21.5 11.962 21.5 15V28"
          stroke="currentColor"
          strokeWidth="1.25"
          strokeOpacity="0.75"
        />

        {/* Keystone notch / Clave de bóveda */}
        <line x1="16" y1="4" x2="16" y2="8" stroke="currentColor" strokeWidth="1.75" />

        {/* Central datum point */}
        <circle cx="16" cy="19" r="1.25" fill="currentColor" />
      </svg>

      {/* Typography: Wordmark + Architectural Stamp */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: layout === 'vertical' ? 'center' : 'flex-start',
          gap: size === 'lg' ? '0.3rem' : '0.2rem',
          transform: layout === 'horizontal' ? (size === 'sm' ? 'translateY(2.5px)' : 'translateY(2px)') : undefined,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-serif, "Newsreader", Georgia, serif)',
            fontSize: size === 'lg' ? '1.85rem' : size === 'md' ? '1.45rem' : '1.18rem',
            fontWeight: 400,
            letterSpacing: '0.04em',
            color: textColor,
            lineHeight: 1,
            display: 'inline-block',
          }}
        >
          Arrendis
        </span>

        {shouldShowSubtitle && (
          <span
            style={{
              fontFamily: 'var(--font-mono, "Space Mono", monospace)',
              fontSize: size === 'lg' ? '0.62rem' : '0.55rem',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--text-muted, #8c827a)',
              lineHeight: 1,
              whiteSpace: 'nowrap',
            }}
          >
            Registro Patrimonial
          </span>
        )}
      </div>
    </div>
  );
}
