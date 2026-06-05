/**
 * Wallet service.
 */
import api from './api';

export interface WalletBalance {
  balance_credits: number;
  updated_at: string;
}

export interface WalletTransaction {
  _id: string;
  user_id: string;
  type:
    | 'welcome_bonus'
    | 'daily_reward'
    | 'trade_buy'
    | 'trade_sell'
    | 'fee_buyer'
    | 'fee_seller'
    | 'refund_transfer'
    | 'engagement_reward'
    | 'adjustment';
  amount: number;
  balance_after: number;
  description_it: string;
  created_at: string;
}

export interface WalletTransactionsList {
  items: WalletTransaction[];
  total: number;
  page: number;
  page_size: number;
}

export async function getBalance(): Promise<WalletBalance> {
  const { data } = await api.get<WalletBalance>('/wallet/balance');
  return data;
}

export async function getTransactions(page = 1, page_size = 20): Promise<WalletTransactionsList> {
  const { data } = await api.get<WalletTransactionsList>('/wallet/transactions', {
    params: { page, page_size },
  });
  return data;
}
