"""Balayage GeckoTerminal : rythme de création de pools par réseau (200 derniers pools au plus).

Usage : python scan_reseaux_gt.py [reseau1 reseau2 ...]
Sortie : scan_reseaux_gt.txt (court) + cache/*.json (3 h).
Source : https://api.geckoterminal.com/api/v2/networks/{id}/new_pools (gratuit, ~30 appels/min).

Limites (à garder en tête en lisant la sortie) :
- GeckoTerminal ne voit que les DEX qu'il indexe : les courbes de launchpad non indexées manquent.
- 10 pages x 20 pools au plus : sur un réseau très actif, la fenêtre couvre quelques heures seulement.
- « actif » et « x5 » sont ici des APPROXIMATIONS sur instantané 24 h (volume total, pas achats seuls) :
  actif ~ volume 24 h >= 440 $ ; x5 ~ variation 24 h >= +400 % avec volume 24 h >= 4 400 $.
  Ce n'est pas la règle de chaleur exacte (bloc +2, achats seuls) : c'est un tri grossier.
"""
from __future__ import annotations

import datetime as dt
import sys
from collections import Counter

from commun import ecrire_txt, en_parallele, get_json

TTL = 3 * 3600
RESEAUX = (
    "megaeth monad arc tempo x-layer fluent igra citrea mezo bot-chain doma hyperevm tron "
    "sui-network ton aptos berachain unichain ink abstract sei-evm sonic avax stable zigchain "
    "katana soneium somnia 0g pharos fogo story plume-network initia hemi movement injective "
    "near stacks aleo rise sonic-svm eclipse bsc"
).split()


def t(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def balayer(reseau: str):
    pools, dex = [], Counter()
    for page in range(1, 11):
        url = f"https://api.geckoterminal.com/api/v2/networks/{reseau}/new_pools?page={page}&include=dex"
        try:
            d = get_json(url, ttl=TTL)
        except Exception as e:
            return {"reseau": reseau, "erreur": str(e)[:80]}
        if not d or not d.get("data"):
            break
        for p in d["data"]:
            a = p["attributes"]
            pools.append(
                {
                    "cree": a.get("pool_created_at"),
                    "vol24": float((a.get("volume_usd") or {}).get("h24") or 0),
                    "var24": float((a.get("price_change_percentage") or {}).get("h24") or 0),
                    "achats24": ((a.get("transactions") or {}).get("h24") or {}).get("buys") or 0,
                    "acheteurs24": ((a.get("transactions") or {}).get("h24") or {}).get("buyers") or 0,
                    "reserve": float(a.get("reserve_in_usd") or 0),
                    "dex": ((p.get("relationships") or {}).get("dex") or {}).get("data", {}).get("id"),
                }
            )
        if len(d["data"]) < 20:
            break
        # assez d'historique : on s'arrête si le plus ancien a plus de 30 jours
        if pools and pools[-1]["cree"] and (dt.datetime.now(dt.UTC) - t(pools[-1]["cree"])).days > 30:
            break
    if not pools:
        return {"reseau": reseau, "erreur": "aucun pool"}
    for p in pools:
        dex[p["dex"]] += 1
    dates = sorted(t(p["cree"]) for p in pools if p["cree"])
    maintenant = dt.datetime.now(dt.UTC)
    duree_j = max((maintenant - dates[0]).total_seconds() / 86400, 1 / 24)
    jeunes = [p for p in pools if p["cree"] and (maintenant - t(p["cree"])).total_seconds() <= 86400]
    return {
        "reseau": reseau,
        "n": len(pools),
        "fenetre_j": duree_j,
        "pools_par_j": len(pools) / duree_j,
        "n_24h": len(jeunes),
        "actifs_24h": sum(1 for p in jeunes if p["vol24"] >= 440),
        "x5_24h": sum(1 for p in jeunes if p["var24"] >= 400 and p["vol24"] >= 4400 and p["var24"] <= 1_000_000),
        "vol24_jeunes": sum(p["vol24"] for p in jeunes),
        "max_acheteurs": max((p["acheteurs24"] for p in jeunes), default=0),
        "dex": dex.most_common(4),
    }


def main():
    reseaux = sys.argv[1:] or RESEAUX
    res = en_parallele(balayer, reseaux, fils=3)
    lignes = [
        f"GeckoTerminal new_pools, {dt.datetime.now(dt.UTC):%Y-%m-%d %H:%M} UTC. Approximations : voir l'en-tête du script.",
        "reseau | pools lus | fenêtre (j) | pools/j | nés <24h | actifs~ <24h | x5~ <24h | vol 24h des nés <24h | max acheteurs | DEX principaux",
    ]
    for r in sorted(res, key=lambda r: -(r.get("pools_par_j") or 0)):
        if "erreur" in r:
            lignes.append(f"{r['reseau']} | ERREUR {r['erreur']}")
            continue
        lignes.append(
            f"{r['reseau']} | {r['n']} | {r['fenetre_j']:.2f} | {r['pools_par_j']:.1f} | {r['n_24h']} | "
            f"{r['actifs_24h']} | {r['x5_24h']} | {r['vol24_jeunes']:,.0f} $ | {r['max_acheteurs']} | {r['dex']}"
        )
    print(ecrire_txt("scan_reseaux_gt.txt", lignes))


if __name__ == "__main__":
    main()
