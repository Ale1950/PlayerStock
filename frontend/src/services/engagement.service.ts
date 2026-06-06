/** Engagement service (Fase 6). */
import api from './api';

export interface StreakState {
  current_streak: number;
  longest_streak: number;
  last_claim_at: string | null;
  can_claim_today: boolean;
  next_reward_estimate?: number;
}
export interface StreakClaimResult {
  claimed: boolean;
  reason?: string;
  current_streak: number;
  longest_streak: number;
  reward_amount?: number;
  reward_tx_id?: string;
  new_nackl_balance?: number;
}
export interface QuizQuestion { id: number; text: string; options: string[]; }
export interface QuizSummary { id: string; title: string; description: string; questions: QuizQuestion[]; active: boolean; }
export interface QuizAttemptResult {
  ok: boolean; correct: number; total: number; score: number; perfect: boolean;
  reward_amount: number; new_nackl_balance?: number;
}
export interface Prediction {
  id: string; athlete_id: string; direction: 'up' | 'down';
  base_price: number; status: 'open' | 'won' | 'lost' | 'void';
  outcome?: 'won' | 'lost' | null;
  settled_price?: number | null;
  created_at: string; expires_at: string; settled_at: string | null;
  reward_amount: number;
}

export async function getStreak() {
  const { data } = await api.get<StreakState>('/engagement/streak');
  return data;
}
export async function claimStreak() {
  const { data } = await api.post<StreakClaimResult>('/engagement/streak/claim');
  return data;
}
export async function getQuizzes() {
  const { data } = await api.get<{ items: QuizSummary[]; count: number }>('/engagement/quizzes');
  return data;
}
export async function submitQuiz(quizId: string, answers: number[]) {
  const { data } = await api.post<QuizAttemptResult>(`/engagement/quizzes/${quizId}/attempt`, { answers });
  return data;
}
export async function getPredictions(status?: string) {
  const { data } = await api.get<{ items: Prediction[]; count: number }>('/engagement/predictions', { params: { status } });
  return data;
}
export async function submitPrediction(athleteId: string, direction: 'up' | 'down') {
  const { data } = await api.post('/engagement/predictions', { athlete_id: athleteId, direction });
  return data;
}

// ───── Gruppo 3a: missioni · sfide · quiz mercato · overview ─────
export interface MissionItem {
  id: string; title: string; description: string;
  progress: number; target: number; completed: boolean; claimed: boolean;
  reward_proposed: { credits: number; nackl: number };
}
export interface ChallengeStanding { rank: number; pseudonym: string; return_pct: number; is_self: boolean; prize_proposed: { credits: number; nackl: number } | null; }
export interface WeeklyChallenge { week_key: string; ends_at: string; metric: string; standings: ChallengeStanding[]; my_rank: number | null; total: number; }
export interface MarketQuiz { id: string; title: string; questions: QuizQuestion[]; already_attempted: boolean; }
export interface NewsItem { type: string; tone: string; title: string; detail: string; }
export interface EngagementOverview {
  streak: StreakState;
  market_quiz: MarketQuiz;
  predictions: { open: number; recent: Prediction[] };
  missions: MissionItem[];
  challenge: WeeklyChallenge;
  news: { items: NewsItem[] };
}

export async function getOverview() {
  const { data } = await api.get<EngagementOverview>('/engagement/overview');
  return data;
}
export async function claimMission(missionId: string) {
  const { data } = await api.post<{ claimed: boolean; credits?: number; nackl?: number }>(`/engagement/missions/${missionId}/claim`);
  return data;
}
