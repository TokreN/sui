# Étape 0 — réseau (31/10/2026, 19:20 UTC)

Les 4 tests du brief, lancés tels quels :

| Test | Code | Remarque |
|---|---|---|
| dexscreener (`/latest/dex/search?q=eth`) | 200 | OK |
| geckoterminal (`/api/v2/networks?page=1`) | 429 puis 200 | 1er essai limité en débit, 3 relances à 20 s : 200, 200, 200 |
| llama (`/v2/chains`) | 200 | OK |
| rpc (`ethereum-rpc.publicnode.com`, `eth_blockNumber`) | 200 | OK |

Résultat : 4 sur 4 joignables (1 sur 4 a d'abord rendu 429, pas un blocage). Pas de « RÉSEAU BLOQUÉ ».

Recherche web : marche (requête test « new blockchain mainnet launch November 2026 », résultats rendus).

Contrainte notée : GeckoTerminal gratuit = environ 30 appels/min. Les scripts le respectent (pause + cache).
