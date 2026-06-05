/** Portfolio service (Fase 4). */
import api from './api';

export interface Position {
  athlete_id: string;
  display_label: string;
  display_initial: string;
  display_lastname: string;
  role: 'POR' | 'DIF' | 'CC' | 'ATT';
  nationality_iso3: string;
  team_fantasy_name: string | null;
  team_color_primary: string | null;
  prezzo_iniziale_crediti: number;
  status: 'ACTIVE' | 'TRANSFERRED' | 'RETIRED';
  quantity: number;
  avg_cost: number;
  cost_basis: number;
  current_price: number;
  current_value: number;
  pnl_abs: number;
  pnl_pct: number | null;
}

export interface PortfolioTotals {
  cash_credits: number;
  positions_value: number;
  positions_cost_basis: number;
  total_equity: number;
  total_pnl_abs: number;
  total_pnl_pct: number | null;
  positions_count: number;
}

export interface PortfolioResponse {
  totals: PortfolioTotals;
  positions: Position[];
}

export interface LeaderboardItem {
  rank: number;
  display_name: string;
  is_self: boolean;
  total_equity: number;
  positions_value: number;
  cash_credits: number;
}

export interface LeaderboardResponse {
  items: LeaderboardItem[];
  self: LeaderboardItem | null;
  total_users: number;
}

export interface PricePoint { ts: string; price: number; }
export interface PriceHistoryResponse { athlete_id: string; points: PricePoint[]; count: number; }

export async function getPortfolio(): Promise<PortfolioResponse> {
  const { data } = await api.get<PortfolioResponse>('/portfolio');
  return data;
}

export async function getLeaderboard(limit = 50): Promise<LeaderboardResponse> {
  const { data } = await api.get<LeaderboardResponse>('/leaderboard', { params: { limit } });
  return data;
}

export async function getPriceHistory(athlete_id: string, limit = 30): Promise<PriceHistoryResponse> {
  const { data } = await api.get<PriceHistoryResponse>(`/athletes/${athlete_id}/price-history`, { params: { limit } });
  return data;
}
