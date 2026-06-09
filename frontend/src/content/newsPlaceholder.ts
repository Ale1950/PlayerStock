export interface NewsItem { source: string; title: string; url: string; }

// PLACEHOLDER statico — il feed RSS reale è uno step separato (vedi DESIGN_SYSTEM §3).
export const NEWS_PLACEHOLDER: NewsItem[] = [
  { source: 'PlayerStock', title: 'Il feed news arriva presto: qui le notizie del giorno.', url: 'https://example.com' },
  { source: 'Mercato', title: 'Analisi dei movimenti di prezzo della settimana.', url: 'https://example.com' },
  { source: 'Community', title: 'Le posizioni più seguite dai trader.', url: 'https://example.com' },
];
