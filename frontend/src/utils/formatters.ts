import { colors } from '@/src/theme/colors';
import { typography } from '@/src/theme/spacing';

/**
 * Prezzo quota in € (migrazione D7). 2 decimali, it-IT (es. 86,30 → "€86,30").
 * Il simbolo "€" è aggiunto dai chiamanti.
 */
export function formatPrice(value: number): string {
  return new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Valore di mercato in €M (Fase 2c) — es. €72,5M. it-IT (virgola decimale).
 * ≥100M → 0 decimali; sotto → 1 decimale. Layer di realismo, separato dal prezzo quota.
 */
export function formatEuroM(valueEur: number | null | undefined): string {
  if (valueEur == null) return '—';
  const m = valueEur / 1e6;
  const dec = m >= 100 ? 0 : 1;
  const num = new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  }).format(m);
  return `€${num}M`;
}

export function formatCredits(value: number): string {
  return new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatInt(value: number): string {
  return new Intl.NumberFormat('it-IT', { maximumFractionDigits: 0 }).format(value);
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
