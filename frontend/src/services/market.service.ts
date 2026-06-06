/** Market service (Fase 3): quote + ordini buy/sell contro la casa. */
import api from './api';

export interface QuoteResponse {
  athlete_id: string;
  prezzo_corrente_eur: number;
  primary_pool_qty: number;
  qty: number;
  buy_cost: number;
  buy_fee: number;
  sell_proceeds: number;
  sell_fee: number;
}

export interface OrderResult {
  side: 'buy' | 'sell';
  qty: number;
  price: number;
  gross: number;
  fee: number;
  cost?: number;
  proceeds?: number;
  new_balance: number;
}

export async function getQuote(athleteId: string, qty: number): Promise<QuoteResponse> {
  const { data } = await api.get<QuoteResponse>(`/market/athletes/${athleteId}/quote`, {
    params: { qty },
  });
  return data;
}

export async function placeOrder(
  athleteId: string, side: 'buy' | 'sell', qty: number,
): Promise<OrderResult> {
  const { data } = await api.post<OrderResult>('/market/orders', {
    athlete_id: athleteId,
    side,
    qty,
  });
  return data;
}

export interface Holding {
  athlete_id: string;
  display_label?: string;
  role?: string;
  quantity: number;
  prezzo_corrente_eur: number;
  valore_corrente_eur: number;
}

export async function getMyHoldings(): Promise<Holding[]> {
  const { data } = await api.get<Holding[]>('/market/holdings');
  return data;
}
