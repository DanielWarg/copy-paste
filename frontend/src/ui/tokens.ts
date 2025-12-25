/**
 * UI Design Tokens - Single Source of Truth
 * 
 * Extracted from archived frontend to ensure 1:1 visual match.
 * All values must match docs/UI_STYLE_TOKENS.md exactly.
 */

export const tokens = {
  // Typography
  fonts: {
    sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'].join(', '),
    serif: ['Merriweather', 'serif'].join(', '),
    mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'].join(', '),
  },
  fontSizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '10px': '0.625rem', // 10px (section labels)
  },
  fontWeights: {
    normal: 400,
    medium: 500,
    bold: 700,
  },
  letterSpacing: {
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },

  // Colors - Light Mode
  colors: {
    light: {
      bg: {
        main: '#fafafa',      // zinc-50
        surface: '#ffffff',    // white
        active: '#f4f4f5',     // zinc-100
        content: 'rgba(250, 250, 250, 0.5)', // zinc-50/50
      },
      text: {
        primary: '#18181b',    // zinc-900
        muted: '#71717a',      // zinc-500
        secondary: '#a1a1aa',  // zinc-400
        medium: '#52525b',     // zinc-600
      },
      border: {
        default: '#e4e4e7',    // zinc-200
        subtle: '#f4f4f5',    // zinc-100
      },
    },
    // Colors - Dark Mode
    dark: {
      bg: {
        main: '#09090b',       // zinc-950
        surface: '#18181b',    // zinc-900
        active: 'rgba(255, 255, 255, 0.1)', // white/10
        content: 'rgba(0, 0, 0, 0.2)', // black/20
        code: 'rgba(24, 24, 27, 0.5)', // zinc-900/50
      },
      text: {
        primary: '#ffffff',    // white
        muted: '#a1a1aa',      // zinc-400
        secondary: '#71717a',  // zinc-500
        label: '#52525b',      // zinc-600
        secondaryText: '#e4e4e7', // zinc-200
      },
      border: {
        default: 'rgba(255, 255, 255, 0.05)', // white/5
        code: '#27272a',       // zinc-800
      },
    },
    // Accent colors (same in both modes)
    accent: {
      status: '#dc2626',       // red-600
      success: '#059669',      // emerald-600
      successHover: '#047857', // emerald-700
      warning: '#f59e0b',      // amber-500
      error: '#ef4444',        // red-500
    },
  },

  // Spacing
  spacing: {
    xs: '0.125rem',   // 2px
    sm: '0.25rem',    // 4px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    '2xl': '1.25rem', // 20px
    '3xl': '1.5rem',  // 24px
    '4xl': '2rem',    // 32px
  },

  // Border Radius
  radius: {
    none: '0',
    sm: '0.125rem',   // 2px
    md: '0.375rem',   // 6px
    default: '0.25rem', // 4px
    full: '9999px',
  },

  // Layout
  layout: {
    sidebarWidth: '16rem',    // 256px (w-64)
    headerHeight: '3.5rem',   // 56px (h-14)
    sidebarHeaderHeight: '4rem', // 64px (h-16)
    contentMaxWidth: '64rem', // 1024px (max-w-5xl)
  },

  // Icons
  icons: {
    xs: '14px',
    sm: '16px',
    md: '18px',
    lg: '20px',
    strokeWidth: 2,
  },

  // Scrollbar
  scrollbar: {
    width: '6px',
    height: '6px',
    thumb: '#52525b',      // zinc-600
    thumbHover: '#71717a', // zinc-500
    track: 'transparent',
    borderRadius: '3px',
  },

  // Transitions
  transitions: {
    fast: '150ms',
    default: '200ms',
  },

  // Opacity
  opacity: {
    disabled: 0.6,
    muted: 0.75,
    hover: 0.9,
    full: 1.0,
  },
} as const;

export type Tokens = typeof tokens;


