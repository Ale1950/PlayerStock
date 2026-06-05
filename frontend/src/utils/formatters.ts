import { colors } from '@/src/theme/colors';
import { typography } from '@/src/theme/spacing';

/**
 * Format a price in Credits (1 Credito = €1 fittizio).
 * Mostra 4 decimali sempre (es. €0.0350).
 */
export function formatPrice(value: number): string {
  return new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(value);
}

export function formatCredits(value: number): string {
  return new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatInt(value: number): string {
  return new Intl.NumberFormat('it-IT').format(value);
}

export function formatChange(deltaPct: number): { text: string; color: string } {
  const sign = deltaPct > 0 ? '+' : '';
  return {
    text: `${sign}${deltaPct.toFixed(2)}%`,
    color: deltaPct > 0 ? colors.up : deltaPct < 0 ? colors.down : colors.textSecondary,
  };
}

export function formatDate(iso: string | Date | null | undefined): string {
  if (!iso) return '—';
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  return new Intl.DateTimeFormat('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).format(d);
}

export function formatDateTime(iso: string | Date | null | undefined): string {
  if (!iso) return '—';
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  return new Intl.DateTimeFormat('it-IT', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(d);
}

export { typography };
