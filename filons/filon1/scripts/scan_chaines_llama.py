"""Balayage DefiLlama : volume DEX par chaîne, tendance 7 j contre 30 j, chaînes nées récemment.

Usage : python scan_chaines_llama.py
Sortie : scan_chaines_llama.txt (court). Cache : ./cache/*.json (12 h).
Source : https://api.llama.fi/overview/dexs/{chaîne} (gratuit, sans clé).
"""
from __future__ import annotations

import urllib.parse

from commun import ecrire_txt, en_parallele, get_json

TTL = 12 * 3600


def fiche(chaine: str):
    url = (
        "https://api.llama.fi/overview/dexs/"
        + urllib.parse.quote(chaine)
        + "?excludeTotalDataChartBreakdown=true"
    )
    try:
        d = get_json(url, ttl=TTL)
    except Exception as e:  # une chaîne en échec ne bloque pas le reste
        return {"chaine": chaine, "erreur": str(e)}
    if not d:
        return {"chaine": chaine, "erreur": "vide"}
    serie = d.get("totalDataChart") or []  # [[ts, volume], ...]
    premier = serie[0][0] if serie else None
    jours = [v for _, v in serie]
    v7 = sum(jours[-7:]) / 7 if len(jours) >= 7 else None
    v30 = sum(jours[-30:]) / 30 if len(jours) >= 30 else None
    return {
        "chaine": chaine,
        "premier_jour": premier,
        "nb_jours": len(serie),
        "v24h": d.get("total24h"),
        "moy7": v7,
        "moy30": v30,
        "t30": d.get("total30d"),
        "t60a30": d.get("total60dto30d"),
        "nb_dex": len(d.get("protocols") or []),
        "dex": sorted(
            ((p.get("displayName") or p.get("name"), p.get("total7d") or 0) for p in d.get("protocols") or []),
            key=lambda x: -x[1],
        )[:5],
    }


def main():
    ov = get_json(
        "https://api.llama.fi/overview/dexs?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true",
        ttl=TTL,
    )
    chaines = ov["allChains"]
    res = [r for r in en_parallele(fiche, chaines, fils=6) if "erreur" not in r]
    import datetime as dt

    def date(ts):
        return dt.datetime.fromtimestamp(ts, dt.UTC).strftime("%Y-%m-%d") if ts else "?"

    lignes = [f"Volume DEX par chaîne (DefiLlama), {len(res)} chaînes sur {len(chaines)} lues."]
    lignes.append("Nées depuis le 01/01/2026 (premier jour de volume DEX), tri par volume moyen 7 j :")
    neuves = [r for r in res if r["premier_jour"] and r["premier_jour"] >= 1767225600]
    for r in sorted(neuves, key=lambda r: -(r["moy7"] or 0)):
        lignes.append(
            f"  {r['chaine']:<22} né {date(r['premier_jour'])}  moy7j {r['moy7'] or 0:>14,.0f} $  "
            f"moy30j {r['moy30'] or 0:>14,.0f} $  dex {r['nb_dex']}  top {r['dex'][:3]}"
        )
    lignes.append("")
    lignes.append("Toutes chaînes > 1 M$/j sur 7 j, tri par ratio moy7/moy30 (chauffe) :")
    actives = [r for r in res if (r["moy7"] or 0) > 1e6 and r["moy30"]]
    for r in sorted(actives, key=lambda r: -(r["moy7"] / r["moy30"])):
        lignes.append(
            f"  {r['chaine']:<22} né {date(r['premier_jour'])}  moy7j {r['moy7']:>14,.0f} $  "
            f"ratio7/30 {r['moy7'] / r['moy30']:.2f}  top {r['dex'][:3]}"
        )
    print(ecrire_txt("scan_chaines_llama.txt", lignes))


if __name__ == "__main__":
    main()
