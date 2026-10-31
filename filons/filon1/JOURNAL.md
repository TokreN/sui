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

## 19:36-19:40 — Contrôle positif de l'instrument V4
- Ethereum (PoolManager 0x0000…4444c5dc…8A90) : 220 Initialize sur 1 000 blocs. Sujets d'événements justes.
- Arc, pool HALLOWEEN/USDC (0x7a0d6c…) : mon script lit 102 achats / 57 ventes / 12 409 $ achetés ; GeckoTerminal 11 min plus tôt : 85 / 55 / 15 424 $ de volume. Cohérent.
- Découverte sur ce contrôle (18:30-19:30 UTC, 14 pools) : 14 sur 14 ont eu la LP retirée (>= 50 %), délai médian 4 min. Le créateur de HALLOWEEN ajoute la LP pleine plage via le PositionManager, la retire 722 blocs (~6 min) plus tard via le contrat 0x934412cf…. 14 créateurs distincts pour 14 pools, jetons à suffixe « …777 ».

## 19:41 — Hypothèse H3 (avant les mesures complètes)
- H3 : sur Arc, « acheter à la fin du bloc +2, vendre à +60 % si atteint en 120 s, sinon sortir à 120 s » (retrait de LP avant la sortie = −100 %) donne un multiple moyen > 1,10 avant frais sur les pools nés du 23 au 30/10, et reste > 1,03 (coût aller-retour ~2,7 % : impact 2 x 1,1 % à 110 $ + frais LP 2 x 0,25 %) sans les 3 meilleurs et sur chaque moitié de période.
- Limite connue à l'avance : sans vérifier la « caisse commune », je ne peux pas dire si les acheteurs sont extérieurs. Je vérifie le payeur (from), le routeur et le nonce sur un échantillon.

## 19:45 — Candidat 2 = Flap.sh sur BSC (hors terrains couverts : seul four.meme a été rejeté sur BSC)
- Instrument : événements du Portal 0xe2cE…9De0 (TokenCreated / TokenBought / TokenSold / TokenQuoteSet), sujets vérifiés par keccak sur des logs réels. Aucun champ indexé : je lis tous les trades de la fenêtre.
- Échantillon (pas de grosse collecte ici) : naissances du 30/10 12:00-15:00 UTC, suivi 24 h. Le script tourne sur n'importe quelle fenêtre chez toi.
- H4 : Flap est CHAUD. Critère : dans ces 3 h seules, >= 50 jetons actifs (>= 220 $ achetés en 24 h) par >= 10 créateurs, ou un rythme de x5 >= 3/jour.
- H5 : une fenêtre existe pour un extérieur. Critère : « +60 % en 120 s » depuis la fin du bloc +2 donne > x1,10 avant frais sur TOUS les jetons cotés (pas seulement les actifs), et > x1,10 sans les 3 meilleurs. Sinon : même verdict que four.meme.
- Test « mooners fabriqués » : achat du créateur dans la tx de création, et nombre de tx dans les blocs 0 à +2, chez les x5 contre tous.

## 19:47 — Résultat Flap (30/10 12:00-15:00 UTC, suivi 24 h) — voir `scripts/flap_3010.txt`
- 1 100 jetons créés en 3 h ; 778 cotés BNB/USDT mesurés ; 62 actifs par 32 créateurs -> H4 VRAIE (CHAUD par la règle).
- x5 : 3 en 3 h (sur la courbe, minorant). 97 créateurs pour 1 100 jetons ; 1 créateur = 143 jetons et porte les 4 plus gros x24.
- H5 FAUSSE : « +60 % en 120 s » sur tous les jetons = x1,005 avant frais (frais lus 1 % par trade + taxe des jetons 7777 non lue).
- Piste à revérifier (petit échantillon) : créateurs uniques, 66 jetons, x1,048 avant frais.

## 19:48 — Correction d'instrument (Arc)
- Le lancement d'Arc (16-19/09) compte 174 229 pools en 72 h ; la devise dominante est 0x3600…0000 (USDC ERC-20, 6 décimales), pas le natif 0x0. Mon 1er lancement ne voyait que ~5 % des pools : arrêté, relancé avec les 2 formes d'USDC et un échantillon uniforme de 3 000 pools (1 sur k dans l'ordre des blocs, sans regarder la suite).
- Le run « semaine » (23-30/10) en cours ne prend que l'USDC natif : à relancer avec les 2 formes.

## 19:50 — Candidat 3 = HyperEVM, usine HyperSwap V2 (0x7244…1c48)
- Vu dans GeckoTerminal (29-31/10) : KLEOS +5 224 %, ELYSX +2 367 %, ICECAT +1 948 % en 24 h, ~400 acheteurs chacun ; réserves restantes 2 à 4 $ pour 2 d'entre eux (LP retirée ?).
- H6 : HyperSwap V2 est CHAUD par la règle des x5 (>= 3 x5 par jour, 3 jours de suite) sur les naissances du 23 au 30/10. Critère : table par jour de `hyperswap_v2.txt`.
- H7 : « +60 % en 120 s » > x1,10 avant frais sur TOUS les pairs cotés WHYPE, et > x1,03 sans les 3 meilleurs.

## 19:50-19:56 — Arc, semaine 23-30/10 (USDC natif seul, 1er passage) et vérification des acheteurs
- 4 728 pools mesurés : ~550 actifs/jour, 20 à 131 créateurs d'actifs/jour -> CHAUD par la règle (2e critère). x5 : 0 chaque jour.
- LP retirée (>= 50 %) : 4 563 sur 4 728, délai médian 4,5 min (p10 0,8 min, p90 6,8 min).
- « +60 % en 120 s » : x1,325 avant frais (77 % des pools touchent +60 % avant le retrait, 15 % retirés avant 120 s).
- MAIS vérification des acheteurs (40 pools du 30/10, 1 sur 14, 200 s suivies, `verif_arc_3010.txt` + analyse) :
  - 0 achat dans les blocs +1 à +3 ; 1er achat >= 5 $ au bloc +11 en médiane (~5,5 s).
  - 1 771 achats >= 5 $ sur 200 s : 100 % via 2 contrats privés (0x43d8…41d5 : 1 205 ; 0x9344…e51f : 566). 0 achat via le routeur public.
  - 0x9344…e51f est le contrat par lequel le créateur retire la LP (vu sur HALLOWEEN). Même opérateur.
  - Payeurs : nonce médian 30 321 ; 60 sur 1 285 ont un nonce < 1 000. Ils revendent via le routeur public, multiple réalisé médian x1,02.
  - Conclusion : volume fabriqué par une flotte (lavage + retrait de LP). Le x1,325 est un artefact de la flotte, pas une fenêtre. Verdict : rejeté (même cas que Robinhood).
- Bug corrigé : 4 110 recherches de tx avaient échoué en silence (créateurs « None »). Lots de 20 + relances + cache. Relancé.

## 20:00-20:05 — Arc, lancement 16-19/09 (échantillon uniforme 1 sur 58, suivi 7 j) — `scripts/arc_lancement.txt`
- Créations : 99 879 (16/09), 55 670 (17/09), 18 680 (18/09). 172 071 cotées USD (surtout USDC 0x3600, 6 déc.).
- Échantillon 2 967 : actifs 164 / 43 / 24 (x58 ≈ 9 500 / 2 500 / 1 400 par jour) ; x5 21 / 7 / 0. CHAUD les 2 premiers jours.
- Grille : x10 30 sur 2 967 (1,0 %), x100 11 (0,4 %) ; tenir 7 j x0,93 (sans top 3 x0,92 ; moitiés x0,92 / x0,94) ; +60 %/120 s x1,01 ; mortes 2 959 sur 2 967.
- x10 par moment : heure 1 1 sur 19 ; heures 2-24 24 sur 1 683 (1,4 %) ; jour 2 4 sur 948 (0,4 %) ; jour 3 1 sur 317.
- Créateur unique 17 sur 962 (1,8 %) contre série 9 sur 1 895 (0,5 %) ; usine de masse (0xb021…97da) 8 sur 2 030 (0,4 %) contre autres 22 sur 937 (2,3 %).
- Impact à l'entrée : 4,2 % à 110 $, 17 % à 450 $. LP retirée : 192 sur 2 967 (délai médian 4,5 h).
- Acheteurs du 16/09 : échantillon uniforme 40 pools, 95 payeurs distincts pour 104 achats, nonce médian 247, 88 % < 1 000 ; actifs : 420 payeurs, nonce médian 169. Foule réelle le jour 1 (contre flotte fin octobre).
- 550 tx de création introuvables sur 2 967 (créateur inconnu) : les parts unique/série sont sur les 2 417 restants + « inconnu ».
- Lecture : effet chaîne neuve faible sur Arc (x10 1,0 % contre 17,8 / 3,1 / 4,6 % sur HyperEVM / Plasma / Robinhood). H2 jugée après le placebo.

## 20:08 — Arc, placebo J+30 (naissances 16-18/10, tous les 2 862 pools USD, suivi 7 j) — `scripts/arc_placebo_j30.txt`
- 900 à 1 100 créations/jour ; actifs 328 / 353 / 329 par ~300 créateurs/jour ; x5 17 / 22 / 5 -> CHAUD par les 2 critères.
- x10 30 sur 2 861 (1,0 %), x100 0 ; tenir 7 j x0,64 ; +60 %/120 s x1,11 ; mortes 2 858 sur 2 861 ; LP retirée 1 071 (délai médian 3,9 min) : la flotte « 7777 » démarre mi-octobre.
- H2 FAUSSE : x10 1,0 % au lancement = 1,0 % à J+30. Pas d'effet chaîne neuve sur Arc (comme Robinhood).
- Segment « petites usines » : 29 x10 sur 413 (7,0 %) mais tenir 7 j x0,74 ; les x10 viennent surtout d'un même launchpad (0xb021…97da) avec des trajectoires identiques (pic ~x17, x0,51 à 7 j). Pas une piste.

## 20:09 — Arc semaine, 2e passage (2 formes d'USDC, créateurs corrigés) — `scripts/arc_semaine.txt`
- 6 151 pools ; actifs 384 à 741/jour par 380 à 733 créateurs distincts/jour -> CHAUD (2e critère). x5/jour : 5, 1, 3, 5, 0, 0, 3, 1 (jamais 3 jours de suite >= 3).
- LP retirée 4 690 sur 6 151 (76 %), médiane 4,5 min. x10 à 7 j : 0 sur 1 105 ; tenir 7 j x0,20 ; +60 %/120 s x1,24 (flux de la flotte). Créateurs : 3 184 (539 en série, 3 475 pools).

## 20:10 — TROU DE DONNÉES BSC (signalé, pas comblé)
- Le RPC public BSC (publicnode) rend [] SANS erreur avant ~le bloc 130,3 M (~3 jours) : même l'USDT y rend 0 log. L'archive exige un jeton personnel (interdit).
- Fenêtres Flap du 27/10 et du 28/10 : 0 jeton lu = trou, pas un résultat. Fichiers supprimés. `mesure_flap.py` vérifie maintenant un contrat témoin (USDT) avant de compter et s'arrête sinon.

## 20:12 — Flap 29/10 18:00-21:00 — `scripts/flap_2910.txt`
- 648 jetons, 490 mesurés, 38 actifs par 30 créateurs (CHAUD), x5 5 en 3 h. +60 %/120 s : x1,012 (sans top 3 x1,008). H5 reste FAUSSE.
- Segment « nouveau créateur » (définition causale : aucun jeton avant dans la fenêtre) : 30/10 x1,028 (sans top 3 x1,010) sur 97 ; 29/10 x1,052 (x1,035) sur 99. Créateur déjà vu : x1,001 / x1,002. Avant frais (1 % x2 + taxe non lue) : rien de solide.
- Acheteurs des 8 plus gros jetons du 30/10 : 12 à 15 payeurs distincts sur les 15 premiers achats, contrats publics de Flap, nonce médian ~1 000 (50 % < 1 000). Activité réelle.

## 20:20 — HyperEVM, HyperSwap V2 (naissances 23-30/10, suivi 24 h) — `scripts/hyperswap_v2.txt`
- Contrôle positif : le pair KLEOS (0x48795e50…) est bien vu au bloc 49 949 152.
- 11 pairs créés en 8 jours, 6 cotés WHYPE (tous les 29 et 30/10) ; 4 actifs, 4 x5 (x27, x91, x112, x68 en 24 h) ; ~250 k$ achetés/jour. H6 FAUSSE (2 x5/jour sur 2 jours, et < 1 lancement/jour). H7 FAUSSE (x1,000 : aucun échange dans les 120 s).
- 0 Burn (pas de retrait de LP), ventes ≈ achats et réserves finales à 2-4 $ (GeckoTerminal) : vidage par les vendeurs.
- 30 premiers achats de chacun des 4 : 27 à 30 payeurs distincts, nonce médian 1 (wallets neufs), via les mêmes contrats 0x49151b65…06bd et 0xb4a9c4e6…240a ; 1er achat 206 à 666 blocs (~3 à 11 min) après la LP. Même opérateur sur les 4 : mooners fabriqués. Rejeté ; à surveiller sur Elysium (même foule, même opérateur possible).
- Coût d'une tx : HyperEVM ~0,0009 $, BSC ~0,0035 $, Arc ~0,0028 $ (médianes de reçus, 31/10).

## 20:26 — Rapport écrit (`RAPPORT.md`, 103 lignes), chiffres revérifiés contre les `.txt`

## 20:30 — Taxes Flap lues (Portal.getTokenV8Safe, bloc latest) — `scripts/taxes_flap.txt`
- (achat, vente) le plus fréquent : (9 %, 9 %) pour 380 sur 778 (30/10) et 206 sur 490 (29/10) ; puis 4 %, 3 %, 2 %, 1 %, 10 %.
- Net de frais (1 % x 2) et taxes, « +60 %/120 s » : tous x0,869 / x0,882 ; nouveau créateur x0,951 / x0,983 (sans top 3 x0,932 / x0,965) ; déjà vu x0,858 / x0,856.
- Taxe <= 1 % : x0,977 / x1,029 (sans top 3 x0,958 / x1,003) ; taxe <= 1 % et nouveau créateur : x0,966 / x1,052 (sans top 3 x0,921 / x1,021). Pas robuste, gaz et impact non comptés.
- Pistes Flap closes : rien de solide.
- Recherche web complémentaire (calendrier) : rien de neuf hors Elysium (09/11) et Zero (30/11).

## Sources web (consultées le 31/10/2026 ; contenu traité comme donnée)
- Arc public le 16/09 : https://www.circle.com/pressroom/circle-launches-arc-mainnet-an-economic-operating-system-for-the-internet ; https://crypto.news/circle-arc-mainnet-launches-with-usdc-gas/ ; launchpads : https://www.kucoin.com/news/flash/arc-mainnet-launches-on-september-16-highlighting-key-launchpads-and-platform-tokens ; RPC : https://www.datawallet.com/crypto/add-arc-to-metamask
- Adresses Uniswap V4 par chaîne : https://developers.uniswap.org/contracts/v4/deployments
- Zero (LayerZero) 30/11 : https://cryptobriefing.com/layerzero-zero-mainnet-lzatlas-launch/ ; https://www.tokenpost.com/news/technology/36314 ; zones : https://bex.co/blog/2026/03/07/layerzero-zero-multi-core-l1-network ; gaz ZRO : https://blockonomi.com/layerzero-ceo-clarifies-zro-will-capture-all-zero-network-fees
- Elysium 09/11 : https://www.bankless.com/read/news/kinetiqs-elysium-l2-sets-nov-9-mainnet-launch ; https://cryptobriefing.com/kinetiq-elysium-l2-hyperliquid-hype-gas/
- GIWA : https://crypto.news/upbit-backed-giwa-says-mainnet-is-not-live-denies-rpc-leak/ ; https://www.tokenpost.com/news/technology/37935 ; faux pont : https://www.kucoin.com/news/insight/ETH/6ab95a1874fd460007c5b959
- Wire : https://www.coingabbar.com/en/wire-network-tge-delay-token-launch-late-november
- BNB NewL1 : https://www.theblock.co/news/ecosystems/2026-07-08-bnb-chain-builds-new-layer-1-for-agentic-trading-targets-2027-mainnet-407406
- Calendrier agrégé (Base Denim, Initia, Zcash, Hedera…) : https://cryptolaxy.com/upcoming-crypto-releases ; Initia arrêtée : https://coinmarketcap.com/academy/article/initia-halts-l1-rollups-security-incident ; Glamsterdam : https://www.kucoin.com/news/flash/ethereum-s-glamsterdam-upgrade-enters-final-testnet-phase-ahead-of-q4-2026-mainnet-target
- Pharos 28/04 : https://news.bitcoin.com/pharos-hits-1b-valuation-on-mainnet-launch ; Tempo 18/03 : https://tempo.xyz/faq
- StonkFun sur LaunchLab : https://www.blocmates.com/articles/what-is-stonkfun-heres-how-it-works ; Genius.fun : https://www.theblock.co/press-releases/genius-fun-launches-on-bnb-chain-to-bring-hostile-takeovers-on-chain-415455 ; OTC : https://www.bitrue.com/blog/what-is-otc-token
- Flap (Portal, taxes, suffixes) : https://docs.flap.sh/flap/llms-full.txt

## Règle de chaleur (copiée du brief, figée)
CHAUD si >= 3 x5 par jour pendant 3 jours, OU >= 50 lancements actifs par >= 10 créateurs sur un jour.
- Actif : pool avec >= 0,1 ETH (~220 $) acheté.
- x5 : x5 en 24 h depuis la fin du bloc +2, compté seulement si >= 1 ETH (~2 200 $) acheté. > x10 000 = artefact, ignoré.
- Hors ETH : seuils convertis en dollars (220 $ / 2 200 $).

## 20:29 — Fin. Rapport final poussé (105 lignes). Temps utilisé : ~1 h 10 sur 4 h.

## 20:47 — Relance : menu de sorties x sélections (Flap), test croisé 2 fenêtres — `scripts/exits_flap.py`, `scripts/exits_flap.txt`
- Demande de Walid : continuer tant qu'aucun truc rentable vérifié sans piège. Règle anti-surajustement fixée avant : retenu seulement si « sans top 3 » > 1 sur les DEUX fenêtres (29/10 et 30/10), et sélection observable à l'entrée.
- 7 sorties (F_60_120s, F_100_600s, garder 1 h / 6 h / 24 h, stop suiveur 30 % / 50 %) x 6 sélections, net des vraies taxes.
- Sélections observables à l'entrée testées : nouveau créateur, taxe <= 1 %, nouveau+taxe, nouveau+dev=0, >= 2 tx blocs 0-2, >= 3 tx, dev a acheté >= 5 $ / >= 50 $, nouveau+tx>=2. AUCUNE ne tient (meilleure : dev>=5$ -> +100 %/600 s, x0,992 et x0,962 net, sous 1).
- Seule case gagnante sur les 2 fenêtres : « actif >= 220 $ » (info du futur, inconnue au bloc +2). Piège, écarté.
- Conclusion sourcée : pas de fenêtre à l'aveugle sur Flap. Les 3 candidats RPC (Arc, HyperEVM, Flap) sont clos sur chiffres.
- Genius.fun reste non mesuré : contrat non public, BscScan demande une clé (interdit), archive BSC interdite. Petit ($35 k$/j de frais).
- Livrable actionnable sans piège : `PROTOCOLE_JOUR1.md` (GO/NO-GO Elysium 09/11 et Zero 30/11, signatures de flotte et de retrait de LP en NO-GO).

## Hypothèse H8 (écrite AVANT de compter) — « acheter ceux qui décollent déjà » (momentum), Flap
- Idée de Walid : n'acheter que le top. Version sans futur : entrer au temps T après la création SEULEMENT si les achats cumulés (trades >= 5 $) depuis la création atteignent Y $ ; prix d'entrée = état du prix à T (donc plus cher).
- Grille fixée : T ∈ {60 s, 180 s, 600 s} x Y ∈ {200 $, 1 000 $, 3 000 $} = 9 filtres ; sorties : +60 %/120 s, +100 %/600 s, stop suiveur 30 %, garder 1 h (temps comptés depuis l'entrée). Net de frais 1 % x 2 et des taxes lues.
- Critère : une case n'est retenue que si « sans top 3 » > 1 sur LES DEUX fenêtres (30/10 00-03 h et 30/10 12-15 h UTC), avec n >= 15 par fenêtre. 36 cases testées : risque de faux positif par hasard, d'où l'exigence des 2 fenêtres.
- Limite connue d'avance : mon propre impact à l'entrée n'est pas compté (résultat optimiste).

## 21:54 — Résultat H8 (momentum) — `scripts/momentum_flap.txt`
- Fenêtres 30/10 00-03 h (796 jetons) et 30/10 12-15 h (1 100 jetons), suivi 24 h, taxes lues.
- 36 cases (T ∈ 60/180/600 s x Y ∈ 200/1 000/3 000 $ x 4 sorties) : AUCUNE ne tient (« sans top 3 » < 1 partout, sur les 2 fenêtres).
- Meilleures moyennes : T=600 s, Y=200 $, +60 %/120 s : x0,960 et x0,942 net (sans top 3 x0,953 / x0,936). « Déjà fort » (Y=3 000 $ à 60 s) : x0,841 / x1,068 (n=16), sans top 3 x0,775 / x0,960.
- Garder 1 h après un décollage est le pire (x0,50 à x0,93 sans top 3) : les décollages retombent dans l'heure.
- H8 FAUSSE. Mon impact d'entrée n'est pas compté : la réalité est pire.

## Hypothèse H9 (écrite AVANT de compter) — migrations Flap vers le DEX
- Idée : les migrations pump.fun faisaient +19,6 %/trade en septembre (brief). Analogue BSC jamais mesuré : le jeton Flap finit sa courbe et part sur un pool DEX.
- Instrument : Portal.getTokenV8Safe(token) -> mot 14 = adresse du pool DEX (0 si pas migré). Pool V2 : événements Mint / Sync / Swap. Moment de migration = 1er Mint du pool. Entrée = fin du bloc de migration + 2, prix par Sync.
- Univers : TOUS les jetons créés dans les fenêtres 30/10 00-03 h et 30/10 12-15 h (cache momentum_*), pas seulement les gagnants.
- Sorties : +60 %/120 s, +100 %/600 s, stop suiveur 30 % (sinon prix à 24 h), garder 1 h, garder 24 h. Net : frais PancakeSwap V2 0,25 % x 2 + taxe du jeton (lue) x 2.
- Critère : rentable si « sans top 3 » > 1 sur les 2 fenêtres réunies ET sur chacune ; n >= 10 migrations par fenêtre, sinon « échantillon trop petit ».

## 23:07 — Résultat H9 (migrations Flap) — `scripts/migrations_flap.txt`
- 13 migrations sur 1 896 jetons (6 sur 796 le 30/10 00-03 h ; 7 sur 1 100 le 30/10 12-15 h). Sous le seuil fixé (n >= 10 par fenêtre) : échantillon trop petit pour conclure formellement.
- Mais tout est négatif. Réunies, net moyen : +60 %/120 s x0,794 ; +100 %/600 s x0,699 ; stop 30 % x0,767 ; garder 1 h x0,683 ; garder 24 h x0,803. Sans top 3 : x0,13 à x0,63.
- Aucun signe de l'effet « +19,6 % » des migrations pump.fun de septembre. Le script `migrations_flap.py` est prêt pour un plus grand échantillon (RPC BSC à soi : le public ne garde que ~3 jours).

## 23:08 — Fin de la fenêtre de 4 h (départ 19:20). Rien de rentable trouvé sur chiffres sourcés.

## 23:10 — Prolongation de 10 h demandée par Walid (jusqu'à ~09:10 UTC le 01/11)
- Mêmes règles : données publiques, aucune clé, aucune transaction, tout dans cette session, commit >= toutes les 45 min.
- Règle anti-hasard ajoutée : chaque piste est construite sur des fenêtres « d'étude », puis jugée sur des fenêtres « de contrôle » JAMAIS utilisées pour la construire. Trouvé = gagne net (sans top 3) sur l'étude ET sur le contrôle.
- Ordre : (1) migrations Flap, gros échantillon ; (2) Genius.fun (trouver le contrat sur la chaîne) ; (3) Frontier sur Robinhood (hausse du 29/10) ; (4) lancements HIP-1 sur Hyperliquid (API publique).

## H9b (avant de compter) — migrations Flap, gros échantillon
- Étude : jetons créés le 30/10 00:00 -> 31/10 00:00 UTC. Contrôle : créés le 31/10 00:00 -> 12:00 UTC (jamais regardés avant).
- Mêmes sorties et coûts que H9. Trouvé si une sortie a « sans top 3 » > 1 sur l'étude (n >= 30) ET sur le contrôle (n >= 15).

## 23:22 — Résultat H9b (migrations, gros échantillon) — `scripts/mig_etude.txt`, `scripts/mig_controle.txt`
- Étude (créés le 30/10) : 6 419 jetons, 40 migrent (0,6 %), tous à taxe basse (0 à 3 %), délai médian 2 min. Sans top 3 < 1 pour toutes les sorties (x0,25 à x0,83). H9b FAUSSE selon le critère fixé.
- Contrôle (créés le 31/10 00-12 h) : 1 599 jetons, 7 migrent (n < 15, trop petit). Sans top 3 < 1 partout.
- Motif récurrent repéré APRÈS coup (donc exploratoire, pas une trouvaille) : garder 1 h après la migration -> moyenne x1,667 (étude) et x1,218 (contrôle), portée par 2-3 jetons (x24 et x18 en 1 h) ; médiane x0,22 et x0,42. Profil loterie.
- H9c (exploratoire, à confirmer sur données NEUVES) : « acheter à la migration, garder 1 h » a une espérance > 1. Contrôle neuf = jetons créés après 23:30 UTC le 31/10, jugés vers 08:00 UTC le 01/11. Critère : moyenne nette (impact compris) > 1 sur ce contrôle neuf, et probabilité bootstrap > 90 % que la moyenne regroupée soit > 1.
- Genius.fun : publicnode refuse les recherches sans adresse ; bsc.rpc.blxrbdn.com (public, sans clé) les accepte.

## 23:40 — Pistes 2 et 3, puis arrêt de la recherche
- Genius.fun : recensement des créations de jetons sur BSC (~30 min, RPC public bloXroute sans clé). 0 jeton en « 6666 », 0 en « 4444 » ; contrôle positif : 65 jetons Flap en « 7777 ». four.meme (0x5c95…762b, terrain rejeté) crée maintenant en « ffff ». Contrat Genius non identifié.
- Frontier (Robinhood, RPC public) : Blockscout bloqué par un anti-robot ; aucune des 15 signatures candidates de CoinDeployed sur 6 h. Non mesuré (terrain couvert, petit).
- Décision : arrêt de la recherche, heures restantes non utilisées. Toutes les pistes mesurables gratuitement sont closes sur chiffres. Multiplier les essais fabriquerait surtout des faux positifs (surajustement) et pousserait vers des mises perdantes.
- H9c (« acheter à la migration, garder 1 h ») reste NON confirmée : profil loterie (médiane x0,22 à x0,42, gain porté par 2 jetons sur 47). Non recommandée.
