export interface NewsItem { source: string; title: string; url: string; icon: string; }

// PLACEHOLDER statico — il feed RSS reale è uno step separato (vedi DESIGN_SYSTEM §3).
// `icon` = nome Ionicons per la thumbnail astratta (nessuna foto/logo reale).
export const NEWS_PLACEHOLDER: NewsItem[] = [
  { source: 'PlayerStock', title: 'Il feed news arriva presto: qui le notizie del giorno.', url: 'https://example.com', icon: 'football-outline' },
  { source: 'Mercato', title: 'Analisi dei movimenti di prezzo della settimana.', url: 'https://example.com', icon: 'stats-chart-outline' },
  { source: 'Community', title: 'Le posizioni più seguite dai trader.', url: 'https://example.com', icon: 'people-outline' },
];
