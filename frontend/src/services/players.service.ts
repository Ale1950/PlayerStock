/**
 * Players service.
 */
import api from './api';

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
  valore_iniziale_crediti: number;
  float_quote: number;
  prezzo_iniziale_crediti: number;
  prezzo_corrente_crediti: number;
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
