/**
 * Players service.
 */
import api from './api';

export interface WeeklyStatsCompact {
  gol: number;
  assist: number;
  parate: number | null;
  presenze: number;
}

export interface AthletePublic {
  _id: string;
  sport_id: string;
  display_initial: string;
  display_lastname: string;
  display_label: string;
  nationality_iso3: string;
  role: 'POR' | 'DIF' | 'CC' | 'ATT';
  age: number | null;
  team_fantasy_id: string;
  team_fantasy_name?: string;
  team_color_primary?: string;
  team_color_secondary?: string;
  weekly_stats?: WeeklyStatsCompact | null;
  valore_iniziale_eur: number;
  float_quote: number;
  primary_pool_qty?: number | null;
  prezzo_iniziale_eur: number;
  prezzo_corrente_eur: number;
  market_value_eur?: number | null;   // valore di mercato €M corrente (Fase 2c)
  status: 'ACTIVE' | 'TRANSFERRED' | 'RETIRED';
}

export interface PlayersListResponse {
  items: AthletePublic[];
  total: number;
  page: number;
  page_size: number;
}

export async function listPlayers(params: {
  sport_id?: string;
  role?: string;
  team_id?: string;
  q?: string;
  page?: number;
  page_size?: number;
}): Promise<PlayersListResponse> {
  const { data } = await api.get<PlayersListResponse>('/players', { params });
  return data;
}

export async function getPlayer(id: string): Promise<AthletePublic> {
  const { data } = await api.get<AthletePublic>(`/players/${id}`);
  return data;
}

export interface TeamPublic {
  _id: string;
  sport_id: string;
  fantasy_name: string;
  city: string;
  color_primary: string;
  color_secondary: string;
  country_iso3: string;
}

export async function listTeams(sport_id = 'calcio'): Promise<TeamPublic[]> {
  const { data } = await api.get<TeamPublic[]>('/teams', { params: { sport_id } });
  return data;
}
