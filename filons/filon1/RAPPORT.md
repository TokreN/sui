# Filon 1 — Lieux neufs : launchpads et chaînes (31/10/2026)

Sources : [L] DefiLlama 31/10 ; [G] GeckoTerminal 31/10 (nouveaux pools sur ~3 j) ; [R] mes mesures RPC, détail dans `scripts/*.txt` ; [W] web, liens dans `JOURNAL.md`.

## 1. Pour Walid
1. **Rien de neuf n'est à la fois chaud, réel et rentable à l'aveugle.** Mesuré au RPC : Arc = flotte qui fabrique le volume puis retire la LP (4 690 pools sur 6 151 en ~4,5 min) ; HyperEVM = mooners d'un seul opérateur ; Flap = médiane plate, queue au créateur en série. Sur Flap, testé 7 sorties x 6 sélections sur 2 fenêtres : la seule case gagnante exige de savoir d'avance qui sera « actif » (info du futur). Pas de plan « achète ça » honnête aujourd'hui.
2. Le seul vrai jeu est à venir : **Elysium (09/11)** et **Zero de LayerZero (30/11)**, les deux seules chaînes neuves datées. Plan complet dans `PROTOCOLE_JOUR1.md` : décision **GO/NO-GO** le jour 1, avec les signatures de flotte et de retrait de LP en déclencheurs de NO-GO. Ce n'est pas une promesse de gain, c'est une règle qui dit quand ne pas jouer.
3. Dates : avant le 09/11 (Elysium), avant le 30/11 (Zero). Sur Elysium surtout, guette les contrats 0x49151b65…06bd et 0xb4a9c4e6…240a : ce sont eux qui fabriquaient les mooners de HyperSwap V2 (même écosystème Hyperliquid).

## 2. Lieux examinés (30 derniers jours, hors terrains couverts)
| Lieu | Né le | Lancements actifs / j | Créateurs | x5 / j | Volume / j | 7 j / 30 j | Verdict |
|---|---|---|---|---|---|---|---|
| Arc (L1 Circle, gaz USDC) | public 16/09/2026 | 384 à 741 [R 23-30/10] | 380 à 733 / j | 0 à 5 [R] | DEX 25,4 M$ [L] | 0,76 | CHAUD par la règle, mais flotte + LP retirée (76 %) : rejeté |
| Flap.sh (BSC) | 2024 (Portal v5) | ~300 à 500 (62 et 38 en 3 h) [R 29-30/10] | ~100 pour 650 à 1 100 jetons / 3 h | ~24 à 40 (minorant) [R] | frais 686 k$ [L] | 0,75 | CHAUD et réel, mais rejeté : x0,87 net de frais et taxes à l'entrée aveugle |
| HyperEVM, HyperSwap V2 | 2025 | 4 en 8 j (6 pairs) [R 23-30/10] | 6 | 2 les 29 et 30/10 [R] | achats ~250 k$ [R] | – | rejeté : < 1 lancement / j, mooners fabriqués |
| Genius.fun (BSC, actions tokenisées) | 16/09/2026 | non mesuré | non mesuré | non mesuré | frais 35 k$ [L] | 2,30 | à suivre : contrat introuvable sans clé |
| StonkFun (Solana) | 25/07/2026 | non mesuré | – | – | frais 192 k$ [L] | 0,69 | couvert : tourne sur LaunchLab [W] |
| OTC (Solana) | 27/08/2026 | non mesuré | – | – | frais 102 k$ [L] | 0,93 | jeton né sur pump.fun ; infra du lanceur non vérifiée |
| Graphite (moteur de bonk.fun) | 18/08/2025 | – | – | – | frais 45 k$ [L] | 1,23 | couvert (LaunchLab) |
| Sapling (Solana, Zcash) | 25/09/2026 | – | – | – | frais 17 k$ [L] | 1,10 | couvert (LaunchLab) |
| Frontier (Robinhood) | 30/07/2026 | – | – | – | frais 23 k$, pic 153 k$ le 29/10 [L] | 4,27 | terrain couvert ; fait daté du 29/10, non mesuré |
| Alt Fun (Hyperliquid) | 14/05/2026 | – | – | – | frais 2,4 k$ [L] | 3,66 | rejeté : trop petit |
| fusi.ng (ETH, Uniswap V4) | 10/09/2026 | – | – | – | frais 2 k$ [L] | 1,29 | sans doute dans ta veille V4 |
| Monad | 24/11/2025 | 0 né en 24 h ; 200 pools « spam » à 0,5 $ le 30/10 [G] | – | 0 | DEX 26,6 M$ ; nad.fun frais 1,5 k$ [L] | 0,78 | rejeté : pas de vrais lancements |
| MegaETH | 09/02/2026 | 1 pool en 2,7 j [G] | – | 0 | DEX 0,70 M$ [L] | 1,14 | rejeté : vide |
| X Layer | 2024 | ~27 pools / j, tous à 19 acheteurs et 0 vendeur [G] | – | 0 | DEX 42,8 M$ [L] | 1,52 | rejeté : ferme de robots |
| TON | 2022 | ~59 pools / j [G] | – | ~1 (approx.) [G] | DEX 3,2 M$ [L] | 0,91 | rejeté : 8,7 k$ max par pool |
| Tron | 2020 | trou de données GT (0 pool rendu) | – | – | DEX 192 M$ ; SunPump frais 376 $ [L] | 2,23 | rejeté : la hausse n'est pas des lancements |
| Tempo (Stripe) | 18/03/2026 | 0 pool en 3 j [G] | – | – | DEX 0,88 M$ [L] | 0,83 | rejeté |
| Unichain | 02/2025 | 1,3 pool / j [G] | – | – | DEX 14,2 M$ [L] | 1,46 | rejeté |
| Fluent | 29/04/2026 | 0 pool en 3 j [G] | – | – | DEX 0,20 M$ [L] | 1,65 | rejeté : trop petit |
| Igra (L2 Kaspa) | 07/04/2026 | 1 pool en 3 j [G] | – | – | DEX 17 k$ [L] | 0,69 | rejeté |
| Pharos | 28/04/2026 | 0 pool en 3 j [G] | – | – | non mesuré | – | rejeté |
| Citrea / Mezo (L2 Bitcoin) | 01/2026 | 0 pool en 3 j [G] | – | – | 57 k$ / 88 k$ [L] | ~1 | rejeté |
| Sui | 2023 | 5 pools / j [G] | – | 0 | DEX 25 M$ [L] | 0,77 | rejeté |
| Aptos (MoveFast) / Injective (RunUp) | 13/10 et 02/10/2026 | – | – | – | frais 2 $ / 199 $ [L] | 0,01 / 0,15 | rejetés : éteints |
| Stable (Pumper) | 24/07/2026 | – | – | – | frais 304 $ [L] | 0,96 | rejeté |
| Spark (L2 Bitcoin, Flashnet) | 2025 | non mesuré | – | – | DEX 69 M$ [L] | 0,99 | non mesuré (non EVM) |

## 3. Calendrier (01/11 → 30/12/2026)
| Quoi | Date (source) | EVM | Gaz | Pont | Ordre des tx | DEX / launchpads | Testnet / RPC | À préparer | Bloquant |
|---|---|---|---|---|---|---|---|---|---|
| Zero (L1 LayerZero) | 30/11, annonce officielle du 20/10 [W] | oui (1re zone EVM sans permission) | ZRO | non trouvé | non trouvé | lzATLAS (> 10 places de marché) ; aucun launchpad annoncé | testnet et RPC publics : non trouvés | ZRO ; scripts V2/V4 ; docs officielles | cible institutionnelle (actions, taux) |
| Elysium (L2 Kinetiq) | 09/11, teaser officiel (Bankless 19/10) [W] | oui (Arbitrum Orbit) | HYPE | HYPE 1:1 depuis HyperEVM | 1 séquenceur | DEX Nest dès le 1er bloc ; Montra, Citadel | testnet depuis le 22/09 | déjà préparé | lien HyperCore ~1 mois après |
| GIWA (L2 Upbit) | aucune date ; démenti officiel fin 09 ; un faux pont a reçu 766 ETH [W] | oui (OP Stack) | ETH | pont OP officiel | 1 séquenceur | rien d'annoncé | testnet Sepolia | ne suivre que les domaines officiels | faux lancements |
| Wire Network | TGE 2e moitié de novembre ; mainnet « selon la liquidité » [W] | non trouvé | non trouvé | non trouvé | non trouvé | non trouvé | non trouvé | rien | rumeur |
| BNB « NewL1 » | testnet public fin 2026, mainnet 2027 [W] | oui | BNB | – | blocs 200 ms | – | testnet seulement | rien avant 2027 | hors fenêtre |

Datés mais pas des lieux neufs : Base Denim le 05/11 (blocs 200 ms) ; Initia redémarre vers le 02/11 après l'exploit du 23/10 ; Glamsterdam (ePBS sur ETH) visé au T4.

## 4. Mesures (point C)
**C1. Arc** (Uniswap V4, tous les pools cotés USDC natif ou ERC-20 ; lancement = échantillon uniforme de 1 sur 58) [R]
| | Lancement 16-18/09 | Placebo J+30 16-18/10 | 23-30/10 |
|---|---|---|---|
| Pools créés / j | 99 879 / 55 670 / 18 680 | 899 à 1 112 | 603 à 1 235 |
| Actifs / j (créateurs) | ~9 500 / ~2 500 / ~1 400 (x58) | 328 à 353 (~300) | 384 à 741 (380 à 733) |
| x5 / j | ~1 200 / ~400 / 0 (x58) | 17 / 22 / 5 | 0 à 5 |
| x10 à 7 j ; x100 | 30 sur 2 967 (1,0 %) ; 11 | 30 sur 2 861 (1,0 %) ; 0 | 0 sur 1 105 ; 0 |
| Tenir 7 j / +60 % en 120 s | x0,93 / x1,01 | x0,64 / x1,11 | x0,20 / x1,19 (x1,24 sur les 6 151) |
| Tenir 7 j sans top 3 ; par moitié | x0,92 ; x0,92 / x0,94 | x0,63 ; x0,71 / x0,57 | x0,19 ; x0,31 / x0,08 |
| Mortes à 7 j | 2 959 sur 2 967 | 2 858 sur 2 861 | 1 105 sur 1 105 |
| x10 heure 1 / h 2-24 / jour 2 / jour 3 | 1 sur 19 / 24 sur 1 683 / 4 sur 948 / 1 sur 317 | 1 sur 45 / 12 sur 1 050 / 15 sur 882 / 2 sur 884 | 0 |
| x10 créateur unique / série | 1,8 % / 0,5 % | 0,7 % / 3,3 % | 0 / 0 |
| x10 usine de masse / petites | 0,4 % / 2,3 % | 0,0 % / 7,0 % (mais tenir 7 j x0,74) | 0 / 0 |
| LP retirée (>= 50 %) | 192 sur 2 967 | 1 071 sur 2 862 | 4 690 sur 6 151, médiane 4,5 min |
| Impact à l'entrée 110 $ / 450 $ | 4,2 % / 17 % | 4,4 % / 18 % | 1,6 % / 6,4 % |
- Aller-retour à 110 $ : gaz 2 x 0,003 $, frais LP 2 x 0,25 % (1 % au lancement), impact 2 x 1,6 % (4,2 % au lancement). Soit ~3,7 % aujourd'hui, ~10 % au lancement.
- Acheteurs du 16/09 : foule réelle (40 pools : 95 payeurs distincts pour 104 achats, nonce médian 247, 88 % < 1 000).
- Acheteurs du 30/10 : flotte (40 pools : 1 771 achats en 200 s, 100 % via 0x43d894e2…41d5 et 0x934412cf…e51f ; ce dernier retire aussi la LP ; nonce médian 30 321 ; 1er achat au bloc +11).
- Le x1,24 du « +60 % en 120 s » est donc le flux de la flotte, pas une fenêtre. Bots dans les blocs 0 à +2 : médiane 0 à 1 tx.
- Verdict : pas d'effet chaîne neuve (x10 1,0 % au lancement comme à J+30), puis volume fabriqué. Rejeté.

**C2. Flap.sh sur BSC** (2 fenêtres de 3 h : 30/10 12-15 h et 29/10 18-21 h UTC, suivi 24 h, tous les jetons créés) [R]
- 1 100 et 648 jetons ; actifs 62 et 38, par 32 et 30 créateurs ; x5 3 et 5 (sur la courbe, minorants). CHAUD, acheteurs réels (12 à 15 payeurs distincts sur les 15 premiers achats des plus gros, nonce médian ~1 000).
- Médiane x24 = 1,0, p90 = 1,02 : 9 jetons sur 10 ne montent pas de 2 %. La queue (20 sur 778 font x2+) appartient surtout à un créateur en série (143 jetons en 3 h, les 4 plus gros x24).
- Taxes lues sur le Portal (`taxes_flap.txt`) : 9 % achat / 9 % vente pour la moitié des jetons.
- **Menu de 7 sorties x 6 sélections, sur les 2 fenêtres indépendamment** (`exits_flap.txt`, `exits_flap.py`), net de taxes. Règle fixée d'avance : retenu seulement si « sans top 3 » > 1 sur CHAQUE fenêtre.
  - Observable à l'entrée (nouveau créateur, taxe <= 1 %, dev a acheté, >= 2 tx aux blocs 0-2, combinaisons) : **aucune case** ne tient. Meilleure (dev >= 5 $ -> +100 %/600 s) : x0,992 et x0,962 net, donc perte.
  - Seule case gagnante sur les 2 fenêtres : sélection « actif >= 220 $ » (F_100_600s sans top 3 x1,175 et x1,102). Mais « actif » = achats sur 24 h = information du futur ; inconnue au bloc +2, et l'attendre déplace l'entrée. Piège, pas une stratégie.
- x10, x100, tenir 7 j : non mesurés (RPC public BSC ne sert que ~3 jours de logs).
- Verdict : réel mais **pas de fenêtre à l'aveugle**. Rejeté sur chiffres sourcés et test croisé 2 fenêtres.

**C3. HyperEVM, HyperSwap V2** (naissances 23-30/10, suivi 24 h) [R]
- 11 pairs créés en 8 jours, 6 cotés WHYPE, tous les 29 et 30/10. Pas CHAUD (< 1 lancement / j).
- 4 sur 6 font x5 en 24 h (x27, x91, x112, x68), ~250 k$ achetés par jour.
- « +60 % en 120 s » : x1,000. Aucun échange les 2 premières minutes ; 1er achat 206 à 666 blocs (~3 à 11 min) après la LP.
- 30 premiers achats de chaque pump : 27 à 30 payeurs, nonce médian 1, via les 2 mêmes contrats. Même opérateur, wallets neufs : mooners fabriqués.
- 0 retrait de LP, mais ventes ≈ achats et réserves finales de 2 à 4 $ [G 31/10] : vidage par les vendeurs.
- Aller-retour : frais V2 0,3 % x 2 (standard, non lu), gaz 2 x 0,0009 $ ; impact non calculé. x10, x100, 7 j : non mesurés (pairs trop jeunes).
- Verdict : rejeté. Utile pour Elysium : même foule, opérateur à guetter.

Limites communes : créateur = expéditeur de la tx de création (550 inconnus sur 2 967 au lancement d'Arc) ; caisse commune non vérifiée ; prix du 31/10 (BNB 706 $, HYPE 88 $) appliqués à toute la période ; « mortes à 7 j » = aucun swap >= 5 $ entre J+6 et J+7, ou prix < 10 % de l'entrée, ou LP retirée.

## 5. Non mesuré, et pourquoi
- Caisse commune (qui finance les wallets) : il faut un explorateur ; explorer.arc.io répond 403, BscScan demande une clé.
- Ventes en échec : invisibles dans les logs. Sur Arc, 0 échec sur 300 reçus ; ailleurs non mesuré.
- Impact sur la courbe Flap : non calculé (paramètres r, h, k lisibles via getTokenV8Safe, formule non implémentée ici).
- BSC avant ~le 28/10 : le RPC public rend une liste vide sans erreur, l'archive exige un jeton. Trou signalé, pas comblé.
- Genius.fun (BSC, né le 16/09, frais 7 j / 30 j : 2,30) : contrat non publié, introuvable sans explorateur à clé.
- Solana (StonkFun, OTC, Sapling) et non-EVM (TON, Spark) : pas d'outil gratuit monté ici. Chiffres DefiLlama seulement.
- Carte des 30 jours hors Arc, Flap et HyperSwap V2 : GeckoTerminal ne rend que ~3 jours de nouveaux pools. Le reste repose sur les volumes et frais DefiLlama, pas sur un comptage de pools.
- Zero : testnet, RPC, ordre des transactions et DEX : rien de public au 31/10.
- Frontier (Robinhood, pic le 29/10) : terrain couvert, non mesuré ici.
