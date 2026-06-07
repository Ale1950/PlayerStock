/**
 * TESTO della guida "Come funziona" — CENTRALIZZATO in un solo posto (facile da editare).
 * Solo contenuto (UI lo rende). Lingua: IT, scritto per chiunque (anche un bambino).
 * Nessuna logica: modificare qui il testo NON tocca motore/trade/economia.
 *
 * Migrazione € (D7): valuta = € virtuali; prezzo quota = valore di mercato / 1.000.000;
 * fondo iniziale €1.000.000; faucet €500/giorno.
 */
import { Ionicons } from '@expo/vector-icons';

type IconName = keyof typeof Ionicons.glyphMap;

export interface GuideSection {
  key: string;
  icon: IconName;
  title: string;
  body: string;
  example?: string;
}

export const HOW_IT_WORKS_INTRO = {
  title: `Cos'è PlayerStock`,
  body: `È un gioco: compri e vendi "quote" dei calciatori con € VIRTUALI (non sono soldi veri, non si prelevano). L'obiettivo è far crescere il tuo saldo scegliendo bene.`,
};

export const HOW_IT_WORKS_SECTIONS: GuideSection[] = [
  {
    key: 'quote',
    icon: 'pie-chart-outline',
    title: '1) Le quote dei giocatori',
    body: `Ogni giocatore è diviso in 1.000.000 di pezzettini chiamati "quote". Ne compri quanti vuoi.`,
    example: `come una torta tagliata in un milione di fettine — tu ne prendi 100.`,
  },
  {
    key: 'prezzo',
    icon: 'pricetag-outline',
    title: '2) Il prezzo della quota (in €)',
    body: `Quanto costa UNA quota, in €. I campioni costano di più, le riserve meno.`,
    example: `una quota di un top ~€86,30, una di una riserva ~€0,80.`,
  },
  {
    key: 'valore',
    icon: 'diamond-outline',
    title: '3) Il valore di mercato (€M)',
    body: `Quanto "vale" tutto il giocatore, come nel calcio vero (es. €80M). È la stessa cosa del prezzo, in grande: valore = prezzo × 1.000.000. Una sola scala, niente confusione.`,
    example: `prezzo quota €90 → valore €90M; prezzo €1 → valore €1M.`,
  },
  {
    key: 'cambia',
    icon: 'trending-up-outline',
    title: '4) Come cambia il prezzo',
    body: `Sale se in tanti comprano quel giocatore, scende se in tanti vendono (e più avanti salirà se gioca bene). Non può però scendere sotto un minimo: il 10% del prezzo di partenza.`,
    example: `se oggi in tanti comprano Rossi, domani la sua quota costa un po' di più; se parte da €5 non scenderà mai sotto €0,50.`,
  },
  {
    key: 'saldo',
    icon: 'cash-outline',
    title: '5) Il tuo saldo in €',
    body: `Sono i soldi del gioco (virtuali, non si incassano). Inizi con €1.000.000 e li usi per comprare.`,
    example: `con €1.000.000 compri quote di tanti giocatori diversi.`,
  },
  {
    key: 'commissione',
    icon: 'cut-outline',
    title: '6) La commissione (7%)',
    body: `Ogni acquisto e ogni vendita trattiene una fettina (3,5% + 3,5%). Serve a tenere il gioco in equilibrio.`,
    example: `compri quote per €100 → ne paghi circa €103,5.`,
  },
  {
    key: 'cap',
    icon: 'lock-closed-outline',
    title: '7) Il limite del 3% (Cap)',
    body: `Di uno stesso giocatore puoi avere al massimo il 3% (30.000 quote). Così nessuno se lo "compra tutto" e bara sul prezzo.`,
    example: `anche se hai tanti €, di Rossi al massimo 30.000 quote.`,
  },
  {
    key: 'attesa',
    icon: 'time-outline',
    title: `8) L'attesa di 7 giorni`,
    body: `Dopo aver comprato devi aspettare 7 giorni prima di rivendere quelle quote (escono prima le più vecchie). Niente compra-e-rivendi al secondo.`,
    example: `compri lunedì → potrai vendere quelle quote dal lunedì dopo.`,
  },
  {
    key: 'disponibilita',
    icon: 'layers-outline',
    title: '9) Disponibilità (quote rimaste)',
    body: `Le quote sono in numero finito. Se finiscono appare "esaurito" e aspetti che qualcuno venda.`,
    example: `se di Rossi le hanno comprate tutte, per ora non puoi comprarne altre.`,
  },
  {
    key: 'portafoglio',
    icon: 'briefcase-outline',
    title: '10) Portafoglio e guadagno/perdita',
    body: `Nel Portafoglio vedi cosa possiedi e se guadagni o perdi rispetto a quanto hai speso.`,
    example: `comprato a €5,00, ora vale €6,30 → sei in guadagno.`,
  },
  {
    key: 'engage',
    icon: 'flame-outline',
    title: '11) Engage: guadagna € giocando',
    body: `Con streak, quiz, pronostici, missioni e sfide guadagni punti che diventano €.`,
    example: `fai il quiz di oggi e indovini → ottieni qualche €.`,
  },
  {
    key: 'scalare',
    icon: 'speedometer-outline',
    title: '12) € dalle attività: a scalare + tetto giornaliero',
    body: `I primi punti del giorno valgono di più, poi sempre meno, e c'è un tetto: massimo €500 al giorno dalle attività. Così l'economia resta sana (è un bonus, non il motore principale).`,
    example: `i primi punti danno più €, gli ultimi pochi; arrivato a €500 al giorno ti fermi.`,
  },
  {
    key: 'nackl',
    icon: 'sparkles-outline',
    title: '13) NACKL (dal mining, in arrivo)',
    body: `Il NACKL è una cosa a parte: si ottiene SOLO dal mining, cioè in base al tempo in cui l'app resta attiva — MAI dalle attività di gioco (quelle danno solo €). È un sottosistema separato con iscrizione propria (opt-in), per ora solo anteprima (non reale). Non si mischia coi tuoi € e non compra quote.`,
    example: `tieni l'app attiva e il NACKL cresce nel tempo; fare quiz o missioni invece dà €, non NACKL.`,
  },
  {
    key: 'classifica',
    icon: 'trophy-outline',
    title: '14) La classifica',
    body: `Mostra chi gioca meglio (chi fa fruttare di più i suoi €), con i soprannomi.`,
    example: `se i tuoi € crescono più degli altri, sali in classifica.`,
  },
  {
    key: 'fantasia',
    icon: 'shield-outline',
    title: '15) Giocatori di fantasia · valuta virtuale',
    body: `Giocatori e squadre sono inventati (gioco di simulazione). I € sono virtuali: nessun valore reale, nessun prelievo.`,
  },
];
