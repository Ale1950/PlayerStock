/**
 * PlayerStock — Theme (dark finance, MVP Fase 1).
 * Provvisorio; design agent rifinirà in Fase 8b.
 */
export const colors = {
  bg: '#0B0F19',
  bgElevated: '#11172A',
  card: '#161B26',
  cardHover: '#1C2233',
  border: '#222A3D',
  borderStrong: '#2F3950',

  textPrimary: '#FFFFFF',
  textSecondary: '#9CA3AF',
  textMuted: '#6B7280',
  textInverted: '#0B0F19',

  accent: '#3B82F6',           // primary
  accentHover: '#2563EB',
  up: '#16C784',                // green for positive
  down: '#EA3943',              // red for negative
  warning: '#F0B90B',

  success: '#16C784',
  danger: '#EA3943',

  // Disclaimer / compliance banner
  bannerBg: '#1F1402',
  bannerBorder: '#3D2810',
  bannerText: '#FFE4A6',
} as const;

export type AppColors = typeof colors;
