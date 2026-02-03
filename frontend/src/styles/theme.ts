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
    bgLight: '#F5F5F5',
    textPrimary: '#1A1A1A',
    textSecondary: '#6B7280',
    border: '#E5E7EB'
  }
} as const;

export const RISK_STYLES = {
  CRITICAL: {
    bg: 'bg-red-50',
    border: 'border-red-500',
    text: 'text-red-900',
    badge: 'bg-red-500 text-white'
  },
  HIGH: {
    bg: 'bg-orange-50',
    border: 'border-[#F3701B]',
    text: 'text-orange-900',
    badge: 'bg-[#F3701B] text-white'
  },
  MEDIUM: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-500',
    text: 'text-yellow-900',
    badge: 'bg-yellow-500 text-black'
  },
  LOW: {
    bg: 'bg-green-50',
    border: 'border-[#53B848]',
    text: 'text-green-900',
    badge: 'bg-[#53B848] text-white'
  }
} as const;
