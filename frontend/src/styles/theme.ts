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
    border: '#1F2937'
  }
} as const;

export const RISK_STYLES = {
  CRITICAL: {
    bg: 'bg-red-500/10',
    border: 'border-red-500',
    text: 'text-red-200',
    badge: 'bg-red-500 text-white'
  },
  HIGH: {
    bg: 'bg-[#F3701B]/10',
    border: 'border-[#F3701B]',
    text: 'text-orange-200',
    badge: 'bg-[#F3701B] text-white'
  },
  MEDIUM: {
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500',
    text: 'text-yellow-200',
    badge: 'bg-yellow-500 text-black'
  },
  LOW: {
    bg: 'bg-[#53B848]/10',
    border: 'border-[#53B848]',
    text: 'text-emerald-200',
    badge: 'bg-[#53B848] text-black'
  }
} as const;
