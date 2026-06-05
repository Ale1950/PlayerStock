/** Reward service (Fase 5).
 *
 * NB: il saldo `is_placeholder=true` NON è NACKL reale (emesso dal protocollo):
 * è un segnaposto dev/MVP. Il NACKL reale arriverà dal miner on-chain.
 */
import api from './api';

export interface RewardBalance {
  amount: number;
  currency: 'NACKL';
  source: string;
  is_placeholder: boolean;
  status?: string;
  network?: string;
}

export interface RewardProviderInfo {
  provider_name: string;
  is_placeholder: boolean;
  network: string;
  wallet_connected: boolean;
  mining_status: string;
}

export interface WalletConnectResponse {
  connected: boolean;
  mining_public_key_preview: string;
}

export async function getRewardBalance(): Promise<RewardBalance> {
  const { data } = await api.get<RewardBalance>('/reward/balance');
  return data;
}

export async function getRewardProvider(): Promise<RewardProviderInfo> {
  const { data } = await api.get<RewardProviderInfo>('/reward/provider');
  return data;
}

export async function connectMiningWallet(miningPublicKey: string): Promise<WalletConnectResponse> {
  const { data } = await api.post<WalletConnectResponse>('/reward/wallet/connect', {
    mining_public_key: miningPublicKey,
  });
  return data;
}
