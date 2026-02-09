// Theme constants aligned with new tailwind.config.ts

export const DK_COLORS = {
  primary: {
    green: '#53B848',
    black: '#0B0B0B'
  },
  alerts: {
    orange: '#F3701B',
    yellow: '#FFB81C',
    red: '#DC2626'
  },
  neutral: {
    bgLight: '#0B0B0D',
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    border: '#2A2A2A'
  }
} as const;

export const RISK_STYLES = {
  CRITICAL: {
    bg: 'hover:bg-dk-red/5',
    border: 'border-l-dk-red',
    text: 'text-dk-red',
    badge: 'bg-dk-red/10 text-dk-red border border-dk-red/20',
    indicator: 'bg-dk-red'
  },
  HIGH: {
    bg: 'hover:bg-dk-orange/5',
    border: 'border-l-dk-orange',
    text: 'text-dk-orange',
    badge: 'bg-dk-orange/10 text-dk-orange border border-dk-orange/20',
    indicator: 'bg-dk-orange'
  },
  MEDIUM: {
    bg: 'hover:bg-dk-yellow/5',
    border: 'border-l-dk-yellow',
    text: 'text-dk-yellow',
    badge: 'bg-dk-yellow/10 text-dk-yellow border border-dk-yellow/20',
    indicator: 'bg-dk-yellow'
  },
  LOW: {
    bg: 'hover:bg-dk-green/5',
    border: 'border-l-dk-green',
    text: 'text-dk-green',
    badge: 'bg-dk-green/10 text-dk-green border border-dk-green/20',
    indicator: 'bg-dk-green'
  }
} as const;
