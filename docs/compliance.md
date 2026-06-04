# Compliance & IP — PlayerStock

> **Non è un parere legale.** Sintesi operativa per lo sviluppo, estratta da `Brief_per_avvocato.md`.
> I profili giuridici vanno validati da un legale (vedi domande aperte in `DECISIONS.md`).

---

## 1. Disclaimer obbligatorio

Da mostrare in **T&C, landing page, footer Home**:

> "PlayerStock è un gioco di simulazione. I riferimenti agli atleti utilizzano iniziali e dati di
> cronaca pubblicamente disponibili. I nomi delle squadre sono di fantasia e non rappresentano
> affiliazioni ufficiali con alcun club professionistico."

---

## 2. Anonimizzazione Livello 2 ("il metodo è l'asset")

Per ogni atleta in UI/API pubbliche, **solo**:
- Iniziale nome + cognome abbreviato (max 8 char): `L. Martín`
- Nazionalità ISO-3: `ARG`
- Ruolo: `POR / DIF / CC / ATT`
- Età
- Squadra **fantasy** (mappa in `PROJECT_SPEC.md` §2)
- Statistiche pubbliche

**Vietato**: foto reali, loghi club ufficiali, nome esteso, nome club esatto.
Nome reale **solo** nel DB interno. Avatar = iniziali stilizzate coi colori della squadra fantasy.

**Razionale**: ridurre il rischio su diritti d'immagine/licenze di lega/club. Il valore
difendibile non sono i dati altrui ma il **metodo** di valutazione/pricing (formula propria su
metriche osservabili pubbliche).

---

## 3. Due economie separate (argomento di qualificazione)

- **Crediti** = punteggio di gioco virtuale, **non** acquistabile con denaro reale, **senza
  cash-out**. Tutta la dinamica "di borsa" avviene qui.
- **NACKL** = token reale di terzi (Acki Nacki), premio di engagement via mining. **Non** compra
  quote. Valore di mercato gestito dall'infrastruttura del terzo.
- Le due economie **non si mescolano mai**.

L'assenza di acquisto-con-denaro e di cash-out è l'argomento principale a favore di
"gioco/intrattenimento di abilità" vs strumento finanziario / azzardo. **Da confermare col legale.**

---

## 4. Strategia IP (sintesi, da validare)

| Asset | Tutela candidata |
|---|---|
| Metodo valutazione + pesi/costanti | **Segreto commerciale** (`Gioco 5.xls` fuori repo; costanti = know-how) |
| Codice sorgente | **Copyright** |
| Nome "PlayerStock" + logo | **Marchio** |
| Storico/metodo | **Data certa** (repo privato + commit; eventuale timestamp/firma) |
| Verso terzi (incl. AN) | **NDA** prima di condividere formule/parametri |

- I parametri riservati **non** vanno in materiali che circolano (brief/pitch).
- `Gioco 5.xls` **non versionato** (vedi `DECISIONS.md` D0.3/D0.6).

---

## 5. Profili da presidiare (token NACKL)

- **MiCA / AML-KYC / fiscale**: abilitare l'accumulo di un token reale può generare obblighi
  anche se non lo emettiamo noi. Da chiarire col legale e nell'accordo con Acki Nacki.
- **GDPR**: registrazione, login Google, profilazione, eventuale KYC legato al token.
- **Minori**: gestione età + age rating store.
- **Store** (Apple 3.1.5(b) / gambling / crypto): preparare la posizione prima del lancio.

---

## 6. Domande legali aperte
Tracciate in `DECISIONS.md` (Q6 qualificazione giuridica; Q1 app_dapp_id AN). Da portare al
legale e ad Acki Nacki ai cancelli decisionali 2–3 della roadmap.
