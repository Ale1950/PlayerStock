/** Match Day #2 — stato evento live (Fase 2, read-only). */
import api from './api';

export interface MatchDaySlateItem {
  athlete_id: string;
  label: string | null;
  role: string | null;
  prezzo: number | null;
}

export interface MatchDayState {
  live: boolean;
  event_id?: string;
  status?: string;
  kind?: 'friendly' | 'tournament_match';
  tournament_id?: string | null;
  tick?: number;
  opens_at?: string;
  closes_at?: string;
  seconds_left?: number;
  slate?: MatchDaySlateItem[];
}

export async function getCurrentMatchDay(): Promise<MatchDayState> {
  const { data } = await api.get<MatchDayState>('/match-day/current');
  return data;
}
