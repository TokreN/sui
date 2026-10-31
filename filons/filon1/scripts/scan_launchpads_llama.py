"""Balayage DefiLlama des launchpads : date de démarrage, frais par jour, tendance 7 j / 30 j, part par chaîne.

Usage : python scan_launchpads_llama.py
Sortie : scan_launchpads_llama.txt (court). Cache : ./cache/*.json (12 h).
Source : https://api.llama.fi/overview/fees + /summary/fees/{slug} (gratuit, sans clé).
Les frais ne sont pas le volume : un launchpad à 1 % de frais fait ~100x ses frais en volume.
"""
from __future__ import annotations

import datetime as dt

from commun import ecrire_txt, en_parallele, get_json

TTL = 12 * 3600
# terrains déjà couverts par Walid : listés pour mémoire, exclus du tri
COUVERTS = {"pump.fun", "Meteora Dynamic Bonding Curve", "LaunchLab", "Bags", "four.meme", "Stockereum",
            "BONK.fun Launchpad", "clanker", "flaunch", "ZORA Coins"}


def date(ts):
    return dt.datetime.fromtimestamp(ts, dt.UTC).strftime("%Y-%m-%d") if ts else "?"


def detail(p):
    slug = p.get("slug") or p["name"].lower().replace(" ", "-")
    try:
        d = get_json(f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees", ttl=TTL)
    except Exception as e:
        return {"nom": p["name"], "erreur": str(e)[:60]}
    if not d:
        return {"nom": p["name"], "erreur": "vide"}
    serie = [(ts, v) for ts, v in (d.get("totalDataChart") or []) if v]
    debut = serie[0][0] if serie else None
    j = [v for _, v in d.get("totalDataChart") or []]
    m7 = sum(j[-7:]) / 7 if j else 0
    m30 = sum(j[-30:]) / 30 if j else 0
    pic = max(serie, key=lambda x: x[1]) if serie else (None, 0)
    # part par chaîne sur 7 j
    parts = {}
    for _, br in (d.get("totalDataChartBreakdown") or [])[-7:]:
        for ch, val in br.items():
            v = val if isinstance(val, (int, float)) else sum(x for x in val.values() if isinstance(x, (int, float)))
            parts[ch] = parts.get(ch, 0) + v
    tot = sum(parts.values()) or 1
    return {
        "nom": d.get("displayName") or p["name"],
        "debut": debut,
        "m7": m7,
        "m30": m30,
        "pic": pic,
        "chaines": sorted(((c, v / tot) for c, v in parts.items() if v / tot >= 0.02), key=lambda x: -x[1]),
    }


def main():
    ov = get_json("https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true", ttl=TTL)
    lps = [p for p in ov["protocols"] if (p.get("category") or "") in ("Launchpad", "Meme")]
    lps = [p for p in lps if (p.get("total30d") or 0) >= 30 * 30]  # >= 30 $/j de frais en moyenne sur 30 j
    res = [r for r in en_parallele(detail, lps, fils=6) if "erreur" not in r]
    lignes = [f"Launchpads DefiLlama (frais >= 30 $/j sur 30 j) : {len(res)}. Couverts marqués [C]."]
    lignes.append("nom | début | frais/j 7j | frais/j 30j | 7j/30j | pic (date, $) | chaînes (part 7 j)")
    for r in sorted(res, key=lambda r: -r["m7"]):
        tag = "[C] " if r["nom"] in COUVERTS else ""
        ratio = r["m7"] / r["m30"] if r["m30"] else 0
        ch = ", ".join(f"{c} {x:.0%}" for c, x in r["chaines"][:4])
        lignes.append(
            f"{tag}{r['nom']} | {date(r['debut'])} | {r['m7']:,.0f} | {r['m30']:,.0f} | {ratio:.2f} | "
            f"{date(r['pic'][0])} {r['pic'][1]:,.0f} | {ch}"
        )
    print(ecrire_txt("scan_launchpads_llama.txt", lignes))


if __name__ == "__main__":
    main()
