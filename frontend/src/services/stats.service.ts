/** Stats service — aggregati interni /api/stats/* (Parte 2 design). */
import api from './api';

export interface Mover { athlete_id: string; display_label?: string | null; var_pct: number | null; }
export interface RoleDist { count: number; min: number; max: number; avg: number; }

export interface MarketOverview {
  active_count: number;
  total_market_cap: number;
  volume_24h: number;
  volume_7d: number;
  top_gainers: Mover[];
  top_losers: Mover[];
  most_traded: { athlete_id: string; volume: number }[];
  price_distribution: Record<string, RoleDist>;
}

export interface ValueDecomposition {
  k_global: number; base_ruolo: number; f_score: number; f_eta: number;
  f_minutaggio: number; f_squadra: number; valore_equo: number;
}

export interface AthleteStats {
  athlete_id: string;
  prezzo_corrente: number;
  market_cap: number;
  valore: number;
  market_value_eur: number | null;   // valore di mercato €M corrente (Fase 2c)
  disponibili: number;
  posseduta_pct: number;
  sold_out: boolean;
  var_24h_pct: number | null;
  var_7d_pct: number | null;
  max: number;
  min: number;
  volume_24h: number;
  volume_7d: number;
  n_holders: number;
  deviazione: number;
  scostamento_vs_equo_pct: number | null;
  value_decomposition: ValueDecomposition;
}

export async function getMarketOverview(): Promise<MarketOverview> {
  const { data } = await api.get<MarketOverview>('/stats/market');
  return data;
}

export async function getAthleteStats(athleteId: string): Promise<AthleteStats> {
  const { data } = await api.get<AthleteStats>(`/stats/athletes/${athleteId}`);
  return data;
}

export type Period = '1S' | '1M' | '3M' | 'all';

export interface Indices {
  return_pct: number; volatility: number; max_drawdown: number; beta: number; sharpe: number;
}
export interface EquityPoint { ts: string; equity: number; }
export interface PricePt { ts: string; price: number; }

export interface PositionAnalytics {
  athlete_id: string;
  display_label: string | null;
  role: string | null;
  quantity: number;
  series: PricePt[];
  delta_week_pct: number | null;
  delta_month_pct: number | null;
  indices: Indices;
}

export interface PortfolioAnalytics {
  period: Period;
  granularity: 'day' | 'week';
  equity: { points: EquityPoint[] };
  portfolio_indices: Indices;
  market_best_player: { athlete_id: string; display_label: string | null; series: PricePt[] } | null;
  best_user: { pseudonym: string; equity: { points: EquityPoint[] }; return_pct: number } | null;
  positions: PositionAnalytics[];
}

export async function getPortfolioAnalytics(period: Period): Promise<PortfolioAnalytics> {
  const { data } = await api.get<PortfolioAnalytics>('/stats/me/analytics', { params: { period } });
  return data;
}

export interface LeaderItem {
  rank: number;
  pseudonym: string;
  is_self: boolean;
  equity: number;
  return_pct: number;
  roi_vs_market_pct: number;
  win_rate: number | null;
  volatility: number;
  return_week_pct: number | null;
  trend: number[];
}
export interface LeaderboardAnalytics {
  items: LeaderItem[];
  total_users: number;
  market_return_pct: number;
  period: Period;
}

export async function getLeaderboardAnalytics(period: Period, limit = 30): Promise<LeaderboardAnalytics> {
  const { data } = await api.get<LeaderboardAnalytics>('/stats/leaderboard-analytics', { params: { period, limit } });
  return data;
}

// Riepilogo personale (assoluto) per il Profilo — dati esistenti, nessun calcolo nuovo.
export interface MyStats {
  equity: number;
  cash_eur: number;
  positions_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_fees: number;
}

export async function getMyStats(): Promise<MyStats> {
  const { data } = await api.get<MyStats>('/stats/me');
  return data;
}
