# Journal — Filon 1 (launchpads et chaînes neuves)

Départ : 31/10/2026 19:20:02 UTC. Fin au plus tard : 23:20 UTC.
Commits prévus : avant 20:05, 20:50, 21:35, 22:20, 23:05.

## 19:20 — Étape 0
- Réseau : 4 sur 4 joignables (GeckoTerminal 429 au 1er essai, puis 200 x3). Voir `reseau.md`.
- Recherche web : OK.
- Pas de sous-agent, tout dans cette session.

## Plan
1. A. Carte du présent : balayage large (DefiLlama chaînes + volumes DEX par chaîne, GeckoTerminal réseaux + nouveaux pools, DEX Screener), puis fiche par lieu (>= 15 lieux hors terrains couverts).
2. B. Calendrier 60 j (01/11 → 30/12/2026) : recherche web + annonces officielles.
3. C. Mesure des 3 meilleurs candidats : événements d'usine via RPC public quand c'est possible, prix via swaps/OHLCV.
4. Rapport `RAPPORT.md` (<= 120 lignes).

## 19:21-19:34 — A, premier balayage (sources du 31/10/2026)
- `scripts/scan_chaines_llama.txt` : volume DEX par chaîne (DefiLlama), 297 chaînes. Nées en 2026 : Robinhood (10/06), Arc (03/06, public 16/09), Tempo (18/03), MegaETH (18/01), Fluent, Igra, Citrea, Mezo, BOT Chain...
- `scripts/scan_launchpads_llama.txt` : 88 launchpads (frais >= 30 $/j). Hors couverts, en tête : Flap.sh (BSC), StonkFun (Solana, infra LaunchLab), OTC (Solana), Graphite (infra bonk.fun = LaunchLab), Genius.fun (BSC, né 16/09), Frontier (Robinhood, pic 29/10), Sapling (Solana, infra LaunchLab).
- `scripts/scan_reseaux_gt.txt` : GeckoTerminal `new_pools` ne couvre que ~3 jours (limite de l'API, pas 30 j). Arc ~669 pools/j sur Uniswap V4 ; BSC ~2 400/j ; Monad 0 pool né en 24 h (dernier le 30/10 06:56 UTC) ; MegaETH 1 pool en 2,7 j ; Tron : 0 pool rendu (trou de données GT, signalé, pas comblé).
- Calendrier (web) : Zero de LayerZero mainnet 30/11/2026 (annonce 20/10) ; Base Denim 05/11 (blocs 200 ms, pas un lieu neuf) ; BNB nouvelle L1 : testnet fin 2026, mainnet 2027 ; GIWA (Upbit) : pas de date ; Initia arrêtée depuis le 23/10 (exploit).

## 19:35 — Hypothèses et critères AVANT de compter (point C)
Candidat 1 = Arc (L1 Circle, gaz en USDC, mainnet public 16/09/2026).
- H1 : Arc est CHAUD aujourd'hui. Critère : sur au moins 1 jour des 7 derniers, >= 50 pools actifs (>= 220 $ achetés) créés par >= 10 créateurs distincts (créateur = expéditeur de la tx d'Initialize), OU >= 3 x5 (achats >= 2 200 $) par jour 3 jours de suite.
- H2 : l'effet « chaîne neuve » a existé sur Arc. Critère : part de x10 (prix max 7 j / prix d'entrée au bloc +2) des pools nés en 72 h > part des pools nés à J+30 (placebo, 16-19/10), écart >= 2 points, et pas porté par 3 jetons seuls.
- Instrument : événements Initialize et Swap du PoolManager Uniswap V4 d'Arc via RPC public. Contrôle positif d'abord : le même instrument sur le PoolManager V4 d'Ethereum doit rendre des pools et des swaps.
- Si l'échantillon est trop gros pour ici : script livré, mesure sur échantillon, biais écrit.

## Règle de chaleur (copiée du brief, figée)
CHAUD si >= 3 x5 par jour pendant 3 jours, OU >= 50 lancements actifs par >= 10 créateurs sur un jour.
- Actif : pool avec >= 0,1 ETH (~220 $) acheté.
- x5 : x5 en 24 h depuis la fin du bloc +2, compté seulement si >= 1 ETH (~2 200 $) acheté. > x10 000 = artefact, ignoré.
- Hors ETH : seuils convertis en dollars (220 $ / 2 200 $).
