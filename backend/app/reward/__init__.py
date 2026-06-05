"""Layer reward NACKL (Fase 5).

IMPORTANTE: il NACKL reale è EMESSO DAL PROTOCOLLO Acki Nacki (no pre-mine, l'app
non lo crea). L'`InternalRewardProvider` produce un saldo PLACEHOLDER dev/MVP — NON
è NACKL reale. Il saldo reale arriva dalla chain (letto via GraphQL) quando il miner
è attivo (dipende da Q1 app_dapp_id + Q5 mining key di test).
"""
