# Design

## Direzione

Minimalismo calmo, superfici profonde, un solo accento. L'interfaccia deve
sparire davanti al contenuto: niente pannelli permanenti, niente decorazioni
gratuite, nessun elemento che non abbia una funzione.

Riferimenti dichiarati: minimalismo di Helium, pulizia delle impostazioni
Windows 11, densità misurata dei browser desktop premium. Nessun logo, colore
o layout di altri browser viene copiato.

## Palette

Tema predefinito: dark. Fonte unica: [`design/tokens.json`](../design/tokens.json).

| Token | Dark | Light |
|---|---|---|
| `bg` | `#11131B` | `#F5F7FC` |
| `toolbar` | `#191D2B` | `#FFFFFF` |
| `sidebar` | `#171B28` | `#EEF1F8` |
| `surface` | `#222738` | `#FFFFFF` |
| `border` | `#30374A` | `#D9DEEC` |
| `text` | `#F2F4FA` | `#12151F` |
| `textSecondary` | `#9299AD` | `#5B6378` |
| `accent` | `#8299FF` | `#5B72E8` |

L'accent è riservato a focus, selezione, progresso e azione primaria. Non viene
usato per decorare. Il testo secondario non scende mai sotto il contrasto
AA sulle superfici di riferimento.

## Tipografia

- Famiglia: Segoe UI Variable / system-ui, nessun font remoto.
- Display: peso 300–400, tracking negativo (-0.03em) solo per orologio e titoli.
- Testo: 13–14 px, interlinea 1.5.
- Etichette: 11 px, uppercase, tracking 0.14em, colore secondario.

## Geometria e movimento

- Raggi: 8 / 12 / 18 / 28 / pill.
- Bordi: 1 px, mai più spessi salvo focus.
- Ombre: solo per elementi sospesi (dialog, pannello), mai decorative.
- Transizioni: 120–260 ms, easing `cubic-bezier(0.22, 1, 0.36, 1)`.
- `prefers-reduced-motion: reduce` disattiva transform e transizioni.

## Nuova scheda

Gerarchia: marchio → orologio → ricerca → scorciatoie.

- Wallpaper a schermo intero con overlay regolabile (0–80%) e luminosità
  (40–120%).
- Nessuna richiesta di rete: preset a gradiente locali, upload locale letto con
  `FileReader` e salvato come data URL (limite 5 MB).
- Ricerca centrale con placeholder esplicito "Cerca con DuckDuckGo o inserisci
  un indirizzo". Invio naviga: URL → sito, testo → DuckDuckGo.
- Scorciatoie: tile con iniziale, nessuna favicon remota (privacy), nome
  troncato, drag & drop e riordino da tastiera (Alt + frecce).
- Aggiunta, modifica ed eliminazione con dialog nativo, validazione solo
  `http`/`https`.
- Pannello "Personalizza" a scomparsa: tema, wallpaper, overlay, luminosità,
  ripristino.
- Stato vuoto: le scorciatoie predefinite sono neutrali, nessun contenuto
  sponsorizzato.

## Accessibilità

- Focus visibile su ogni controllo, 2 px accent + offset.
- Ruoli e label ARIA per ricerca, griglia, dialog.
- Navigazione da tastiera completa; il drag & drop ha un'alternativa.
- Contrasto testo ≥ 4.5:1 nelle combinazioni previste.
- Animazioni disattivabili dal sistema.

## Stati

| Elemento | Default | Hover | Focus | Attivo |
|---|---|---|---|---|
| Tile | superficie 10% | bordo accent, -2 px | ring 2 px | scala 0.98 |
| Pulsante icona | trasparente | superficie 12% | ring | superficie 18% |
| Campo ricerca | bordo 1 px | bordo più chiaro | bordo accent + ring | — |
| Pannello | chiuso | — | — | tradotto, scrim visibile |

## Cosa non si fa

- Animazioni invasive o parallax.
- Blur eccessivo o vetro su tutto.
- Icone a colori multipli: stroke monocromatico, accent solo nello stato attivo.
- Testo decorativo, citazioni, meteo o notizie nella nuova scheda.
