# Protocole jour 1 — Elysium (09/11) et Zero (30/11)

But : décider **GO / NO-GO** le jour du lancement, sur données publiques, sans se faire piéger. Ce n'est pas une promesse de gain : c'est une règle qui dit quand NE PAS jouer. Walid exécute les transactions lui-même ; moi je mesure.

Pourquoi ce protocole et pas un « achète ça » : sur les 3 lieux vivants mesurés (Arc, HyperEVM, Flap), aucun ne donne de fenêtre à l'aveugle net de coûts (voir `RAPPORT.md`). Les signatures de ces échecs deviennent ici les déclencheurs de NO-GO.

## La veille (préparer, ne rien signer)
- RPC public officiel du lieu + chain id, vérifiés sur le site officiel (pas un domaine ressemblant).
- Adresses : PoolManager Uniswap V4 et/ou usine V2 du DEX du jour 1, routeur public, jeton de gaz (HYPE pour Elysium, ZRO pour Zero), stable de cotation.
- Jeton de gaz déjà ponté côté Walid, petit montant. Tester un aller-retour à 0,05 ETH-équiv **sur un pool établi** pour lire le gaz et l'impact réels.
- Lancer `scan_reseaux_gt.py` et `mesure_v4.py` / `mesure_v2.py` à blanc sur le testnet ou un pool témoin : vérifier que l'instrument rend des pools (contrôle positif).

## Heure 1 (mesurer, décider)
Lancer la mesure sur la 1re heure de naissances, suivi 1 h. Lire, pour les pools « actifs » (≥ ~220 $ achetés) :
1. Nombre de pools actifs et de **créateurs distincts**.
2. Part des pools dont la **LP est retirée** (>= 50 %) dans l'heure.
3. **Qui paie** les 20 premiers achats : nombre de contrats routeurs distincts, nonce médian des payeurs.
4. Impact lu à 0,05 puis 0,2 ETH-équiv.

## Règle NO-GO (un seul critère suffit → on ne joue pas)
- LP retirée sur **> 30 %** des pools actifs (signature Arc : 76 %).
- **>= 80 %** des premiers achats passent par **<= 2 contrats** (signature Arc/HyperEVM : flotte).
- **Nonce médian** des premiers payeurs **< 20** (wallets neufs = flotte ; HyperEVM : nonce médian 1).
- **< 10 créateurs distincts** sur l'heure 1 extrapolée au jour.
- Impact à 0,05 ETH **> 3 %** (tu paies déjà la fenêtre à l'entrée).
- Un seul opérateur porte > la moitié des pools actifs.

## Si GO (aucun NO-GO déclenché)
- Entrée à la **fin du bloc +2**, taille **0,05 ETH-équiv** d'abord (jamais le bloc 0).
- Sortie, choisie sur l'heure 1 **hors les 3 meilleurs jetons** (sinon tu te cales sur le bruit) : garder la règle qui, sur cette heure 1, rend > 1 net de coûts **sans les 3 meilleurs**. Par défaut, **stop suiveur 30 %** (a donné les meilleurs « sans top3 » dans mes tests), repli « +60 % en 120 s ».
- **Revente prouvée** : avant d'élargir, vérifier qu'au moins 3 extérieurs de ta taille ont **vendu avec succès** (pas seulement acheté) dans l'heure. Une revente bloquée = −100 %.
- Monter à 0,2 ETH seulement si l'impact reste < 3 % et si la revente est prouvée. Plafond 0,2 ETH.

## Après (ne pas confondre chauffe et fin de fenêtre)
- Re-mesurer à H+6, H+24, puis chaque jour. Fenêtre présumée 2-4 semaines, mais :
- **Placebo J+7** : refaire la grille sur les pools nés à J+7. Si la part de x10 à J+7 ≈ celle du jour 1, il n'y a pas d'effet « lieu neuf » (cas Arc et Robinhood) → sortir.
- Arrêter dès que la LP retirée dépasse 30 % des actifs, ou que les premiers acheteurs redeviennent une flotte (c'est ainsi qu'Arc est passé de foule réelle le 16/09 à flotte fin octobre).

## Outils
`mesure_v4.py` (Uniswap V4), `mesure_v2.py` (forks V2), `verif_acheteurs_v4.py` (qui paie / revente), `exits_flap.py` (menu de sorties). Tous : `RPC_URL` en variable d'environnement, aucune clé, cache `.json`. Voir `scripts/LISEZMOI.md`.
