# Scripts du filon 1

Python 3.13, bibliothèque standard seulement, aucune clé. RPC dans `RPC_URL`. Cache JSON dans `./cache` (ignoré par git). Chaque script écrit un `.txt` court à côté de lui.

| Script | Ce qu'il fait | Exemple |
|---|---|---|
| `scan_chaines_llama.py` | Volume DEX par chaîne, chaînes nées en 2026, tendance 7 j / 30 j (DefiLlama) | `python scan_chaines_llama.py` |
| `scan_launchpads_llama.py` | Launchpads : début, frais/j, tendance, part par chaîne (DefiLlama) | `python scan_launchpads_llama.py` |
| `scan_reseaux_gt.py` | Rythme de nouveaux pools par réseau (GeckoTerminal, ~3 j seulement) | `python scan_reseaux_gt.py arc megaeth` |
| `mesure_v4.py` | Tous les pools Uniswap V4 d'une fenêtre : actifs, x5, x10, tenir 7 j, +60 %/120 s, retraits de LP, créateurs, usines | voir ci-dessous |
| `mesure_v2.py` | Même chose pour une usine Uniswap V2 (Sync, Burn, Mint) | voir ci-dessous |
| `mesure_flap.py` | Flap.sh (Portal BSC) : jetons créés, actifs, x5 sur la courbe, +60 %/120 s | voir ci-dessous |
| `filtre_pieges.py` | Avant un achat : NO-GO si flotte, LP retirée, wallets neufs, coût de départ > 8 %, créateur en série | `RPC_URL=https://bsc-rpc.publicnode.com python filtre_pieges.py flap --token 0x… --mise 105` |
| `verif_acheteurs_v4.py` | Premiers acheteurs d'un échantillon de pools V4 : payeur, routeur, nonce, revente | voir ci-dessous |

Commandes utilisées le 31/10/2026 :
```bash
RPC_URL=https://rpc.mainnet.arc.io python mesure_v4.py --pm 0x8366a39CC670B4001A1121B8F6A443A643e40951 --debut 2026-10-23T00:00 --fin 2026-10-31T00:00 --suivi 24 --ids-par-appel 300 --quote 0x0000000000000000000000000000000000000000:1:18,0x3600000000000000000000000000000000000000:1:6 --nom arc_semaine
RPC_URL=https://rpc.mainnet.arc.io python mesure_v4.py --pm 0x8366a39CC670B4001A1121B8F6A443A643e40951 --debut 2026-09-16T00:00 --fin 2026-09-19T00:00 --suivi 168 --ids-par-appel 300 --echantillon 3000 --quote 0x0000000000000000000000000000000000000000:1:18,0x3600000000000000000000000000000000000000:1:6 --nom arc_lancement
RPC_URL=https://bsc-rpc.publicnode.com python mesure_flap.py --debut 2026-10-30T12:00 --fin 2026-10-30T15:00 --suivi 24 --prix-natif 706 --nom flap_3010
RPC_URL=https://hyperliquid-json-rpc.stakely.io python mesure_v2.py --usine 0x724412c00059bf7d6ee7d4a1d0d5cd4de3ea1c48 --quote 0x5555555555555555555555555555555555555555:88:18 --debut 2026-10-23T00:00 --fin 2026-10-31T00:00 --suivi 24 --pas 1000 --fils 3 --nom hyperswap_v2
RPC_URL=https://rpc.mainnet.arc.io python verif_acheteurs_v4.py --pools cache/arc_semaine_pools.json --pm 0x8366a39CC670B4001A1121B8F6A443A643e40951 --routeur 0x4fcA4a51Ab4F23A7447b3284fBd7D73289A89Fb1 --jour 2026-10-30 --n 40 --nom verif_arc_3010
```

Pièges connus :
- Le RPC public BSC ne sert que ~3 jours de logs et rend une liste vide sans erreur au-delà. `mesure_flap.py` s'arrête alors avec « TROU DE DONNÉES ». Pour plus d'historique : ton propre nœud.
- Sur Arc, l'USDC existe en natif (0x0, 18 décimales) et en ERC-20 (0x3600…0000, 6 décimales) : passe les deux dans `--quote`.
- Le RPC public HyperEVM (rpc.hyperliquid.xyz) coupe à 5 s : préfère hypurrscan ou stakely (1 000 blocs max par appel).
- `--echantillon N` prend 1 pool sur k dans l'ordre des blocs : uniforme, sans information du futur. Multiplie les totaux par k.
