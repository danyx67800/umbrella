# Sicurezza e privacy

## Modello

Umbrella eredita il modello di sicurezza di Chromium e non lo indebolisce.
Le uniche modifiche ammesse sono additive e verificabili.

Protezioni mantenute:

- Site Isolation e processi renderer separati;
- sandbox Win32 e job object;
- Network Service e validazione dei certificati;
- Safe Browsing (non disattivato per "velocità");
- HTTPS-first e gestione errori di certificato;
- permission manager e content settings;
- profili off-the-record per la navigazione privata;
- aggiornamenti dei componenti firmati da Chromium.

Non sono ammesse patch che disattivino questi sistemi, cambino lo user agent
per aggirare controlli o alterino le informazioni di compatibilità dei siti.

## Dati e telemetria

Umbrella **non aggiunge**:

- analytics o telemetria proprietaria;
- pubblicità, notizie sponsorizzate, contenuti promozionali;
- upload di cronologia, preferiti, URL o contenuto delle pagine;
- account proprietari o sincronizzazione remota.

La nuova scheda non effettua richieste di rete: wallpaper e scorciatoie sono
locali. Le lettere delle scorciatoie sostituiscono le favicon remote per non
rivelare i siti visitati a terzi.

## Connessioni di rete ereditate da Chromium

Queste connessioni esistono nel browser e non sono state rimosse. Sono
documentate perché l'utente possa verificarle e, dove previsto, disattivarle.

| Servizio | Scopo | Controllo |
|---|---|---|
| Safe Browsing | reputazione URL/file | impostazioni privacy |
| Component updater | liste e componenti | aggiornamenti |
| Variations | configurazione esperimenti | non configurabile |
| DNS/HTTPS probing | risoluzione e upgrade | impostazioni rete |
| Search suggestions | suggerimenti omnibox | impostazioni motore |
| Certificate revocation | stato certificati | impostazioni sicurezza |

Le richieste di ricerca vanno al motore scelto (DuckDuckGo di default) solo
quando l'utente cerca o quando i suggerimenti di ricerca sono attivi.

## Navigazione privata

Usa profili off-the-record nativi. Cookie, cache e storage sono separati e
temporanei; la cronologia non viene registrata nel profilo persistente. I dati
del contesto privato vengono eliminati alla chiusura dell'ultima finestra
privata, secondo il comportamento Chromium.

Limiti noti, ereditati e non nascosti:

- il provider di rete e il sito possono comunque vedere il traffico;
- i download scelti dall'utente restano su disco;
- le estensioni con permessi ampi possono osservare attività;
- il private mode non è un proxy anonimizzante.

## Blocco tracker e pubblicità

Pianificato in Fase 5 come `URLLoaderThrottle` nel Network Service con liste
di filtri versionate e aggiornabili. Non è implementato in 0.1.0 e non viene
pubblicizzato come attivo. La UI mostrerà lo stato reale e il numero di
richieste bloccate solo quando la funzione esisterà.

## Permessi

Microfono, fotocamera, geolocalizzazione, notifiche, clipboard, download
automatici e gli altri permessi supportati restano gestiti da Chromium. La UI
Umbrella per la revoca arriva in Fase 4; fino ad allora si usa la pagina
impostazioni nativa, che non viene rimossa.

## Segnalazione vulnerabilità

Non aprire issue pubbliche per vulnerabilità sfruttabili. Contattare il
maintainer del repository privatamente e allegare:

- versione Umbrella e tag Chromium;
- passi di riproduzione;
- impatto stimato;
- eventuale prova di concetto minimizzata.

Le vulnerabilità di Chromium vanno segnalate anche a upstream secondo la
policy del progetto Chromium.
