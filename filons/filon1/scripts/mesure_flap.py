"""Mesure du launchpad Flap.sh (courbe de liaison) à partir des événements du contrat Portal.

Compte TOUS les jetons créés (TokenCreated), pas les survivants.
RPC : variable d'environnement RPC_URL (BSC par défaut : https://bsc-rpc.publicnode.com marche sans clé).

Exemple (jetons nés le 30/10/2026 entre 12:00 et 15:00 UTC, suivi 24 h, BNB à 706 $) :
  RPC_URL=https://bsc-rpc.publicnode.com python mesure_flap.py --debut 2026-10-30T12:00 --fin 2026-10-30T15:00 \
      --suivi 24 --prix-natif 706 --nom flap_3010

Événements (vérifiés par keccak sur des logs réels le 31/10/2026) :
  TokenCreated(uint256 ts, address creator, uint256 nonce, address token, string name, string symbol, string meta)
  TokenBought / TokenSold(uint256 ts, address token, address trader, uint256 amount, uint256 quote, uint256 fee, uint256 postPrice)
  TokenQuoteSet(address token, address quote)
Aucun champ indexé : on lit TOUS les achats/ventes de la fenêtre puis on filtre localement.

Limites : seules les transactions sur la courbe sont suivies. Après migration vers le DEX, les plus hauts
ne sont plus vus (x5 / x10 = minorants). Les taxes des jetons à taxe (suffixe 7777 sur BSC) ne sont pas lues.
Définitions identiques à mesure_v4.py (entrée fin du bloc +2, poussière < 5 $, actif >= 220 $, x5 si >= 2 200 $ achetés).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
import sys
from collections import Counter, defaultdict

from commun import CACHE_DIR, ecrire_txt, en_parallele, rpc, sujet

PORTAL_BSC = "0xe2cE6ab80874Fa9Fa2aAE65D277Dd6B8e65C9De0"
CREE = sujet("TokenCreated(uint256,address,uint256,address,string,string,string)")
ACHAT = sujet("TokenBought(uint256,address,address,uint256,uint256,uint256,uint256)")
VENTE = sujet("TokenSold(uint256,address,address,uint256,uint256,uint256,uint256)")
COTE = sujet("TokenQuoteSet(address,address)")
# cotations en dollars connues sur BSC (adresse -> prix $) ; le natif (0x0) prend --prix-natif
DOLLARS = {
    "0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d": 1.0,  # USD1
    "0x55d398326f99059ff775485246999027b3197955": 1.0,  # USDT (BSC)
    "0x0782b6d8c4551b9760e74c0545a9bcd90bdc41e5": 1.0,  # lisUSD
}


def h2i(x):
    return int(x, 16)


def mot(d, i):
    return int(d[2 + 64 * i: 2 + 64 * (i + 1)], 16)


def ts_bloc(b):
    return h2i(rpc("eth_getBlockByNumber", [hex(b), False], cache=True)["timestamp"])


def bloc_a(ts, tete):
    lo, hi = 1, tete
    while lo < hi:
        m = (lo + hi) // 2
        if ts_bloc(m) < ts:
            lo = m + 1
        else:
            hi = m
    return lo


def logs(adr, topics, de, a, pas, fils):
    tr = [(x, min(x + pas - 1, a)) for x in range(de, a + 1, pas)]
    out = []
    for r in en_parallele(lambda t: rpc("eth_getLogs", [{"address": adr, "fromBlock": hex(t[0]), "toBlock": hex(t[1]), "topics": topics}]), tr, fils=fils):
        out.extend(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", default=PORTAL_BSC)
    ap.add_argument("--debut", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--suivi", type=float, default=24)
    ap.add_argument("--prix-natif", type=float, required=True, help="prix du jeton natif en $ (BNB, OKB, MON...)")
    ap.add_argument("--pas", type=int, default=9999)
    ap.add_argument("--fils", type=int, default=6)
    ap.add_argument("--nom", required=True)
    a = ap.parse_args()

    t0 = int(dt.datetime.fromisoformat(a.debut).replace(tzinfo=dt.UTC).timestamp())
    t1 = int(dt.datetime.fromisoformat(a.fin).replace(tzinfo=dt.UTC).timestamp())
    t2 = t1 + int(a.suivi * 3600)
    tete = h2i(rpc("eth_blockNumber", []))
    b0, b1 = bloc_a(t0, tete), bloc_a(t1, tete)
    b2 = bloc_a(t2, tete) if t2 < ts_bloc(tete) else tete
    print(f"blocs {b0} -> {b1}, suivi -> {b2}", file=sys.stderr)

    jetons = {}
    for l in logs(a.portal, [CREE], b0, b1 - 1, a.pas, a.fils):
        d = l["data"]
        tok = "0x" + d[2 + 64 * 3 + 24: 2 + 64 * 4]
        jetons[tok] = {"jeton": tok, "createur": "0x" + d[2 + 64 + 24: 2 + 64 * 2], "ts": mot(d, 0),
                       "bloc": h2i(l["blockNumber"]), "tx": l["transactionHash"], "cote": "0x" + "0" * 40, "trades": []}
    for l in logs(a.portal, [COTE], b0, b1 - 1, a.pas, a.fils):
        d = l["data"]
        tok = "0x" + d[2 + 24: 2 + 64]
        if tok in jetons:
            jetons[tok]["cote"] = "0x" + d[2 + 64 + 24: 2 + 128]
    print(f"jetons créés : {len(jetons)}", file=sys.stderr)

    n_trades = 0
    for sens, top in ((1, ACHAT), (-1, VENTE)):
        for l in logs(a.portal, [top], b0, b2, a.pas, a.fils):
            d = l["data"]
            tok = "0x" + d[2 + 64 + 24: 2 + 128]
            j = jetons.get(tok)
            n_trades += 1
            if not j:
                continue
            j["trades"].append((h2i(l["blockNumber"]), h2i(l["logIndex"]), mot(d, 0), sens, mot(d, 4), mot(d, 6),
                                "0x" + d[2 + 128 + 24: 2 + 192], l["transactionHash"], mot(d, 5)))
    print(f"achats/ventes lus dans la fenêtre : {n_trades}", file=sys.stderr)

    # prix initial de la courbe (par cotation) : plus petit postPrice vu au 1er trade
    init = defaultdict(list)
    for j in jetons.values():
        if j["trades"]:
            j["trades"].sort()
            init[j["cote"]].append(j["trades"][0][5])

    res = []
    for j in jetons.values():
        q = j["cote"]
        if q == "0x" + "0" * 40:
            px = a.prix_natif
        elif q in DOLLARS:
            px = DOLLARS[q]
        else:
            continue
        tr = j["trades"]
        ent_bloc = j["bloc"] + 2
        e = None
        for t in tr:
            if t[0] <= ent_bloc:
                e = t[5]
        if e is None:
            e = min(init[q]) if init[q] else None
        if not e:
            continue
        dev = sum(t[4] for t in tr if t[7] == j["tx"] and t[3] == 1) / 1e18 * px
        m24 = m120 = e
        p120 = e
        t160 = None
        ach = ven = 0.0
        na = nv = 0
        for t in tr:
            if t[0] <= ent_bloc:
                continue
            dtc = t[2] - j["ts"]
            u = t[4] / 1e18 * px
            if dtc <= 120:
                p120 = t[5]
            if u < 5:
                continue
            if dtc <= 120:
                m120 = max(m120, t[5])
                if t[5] >= 1.6 * e and t160 is None:
                    t160 = dtc
            if dtc <= 86400:
                m24 = max(m24, t[5])
                if t[3] == 1:
                    ach += u
                    na += 1
                else:
                    ven += u
                    nv += 1
        res.append({
            "jeton": j["jeton"], "createur": j["createur"], "ts": j["ts"], "cote": q, "achats24": round(ach, 2),
            "ventes24": round(ven, 2), "n_ach": na, "n_ven": nv, "x24": m24 / e, "s60": 1.6 if t160 is not None else p120 / e,
            "dev_achat": round(dev, 2), "tx_blocs_0_2": len({t[7] for t in tr if t[0] <= ent_bloc}),
            "frais_pct": (100 * st.median([t[8] / t[4] for t in tr if t[4]]) if tr else None),
        })

    with open(os.path.join(CACHE_DIR, f"{a.nom}_jetons.json"), "w", encoding="utf-8") as f:
        json.dump(res, f)
    L = [f"{a.nom} : Portal {a.portal}, naissances {a.debut} -> {a.fin} UTC, suivi {a.suivi} h, natif {a.prix_natif} $.",
         f"Jetons créés : {len(jetons)} ; mesurés (cotés natif ou dollar) : {len(res)} ; trades lus : {n_trades}."]
    if res:
        heures = max((t1 - t0) / 86400, 1e-9)
        act = [r for r in res if r["achats24"] >= 220]
        x5 = [r for r in res if 5 <= r["x24"] <= 10000 and r["achats24"] >= 2200]
        cre = Counter(r["createur"] for r in res)
        L.append(f"Actifs (>= 220 $ achetés en 24 h) : {len(act)} sur {len(res)}, par {len({r['createur'] for r in act})} créateurs ; "
                 f"rythme ~{len(act) / heures:.0f} actifs/jour.")
        L.append(f"x5 en 24 h (>= 2 200 $ achetés, sur la courbe) : {len(x5)} ; rythme ~{len(x5) / heures:.1f} par jour.")
        L.append(f"Créateurs : {len(cre)} ; en série (>= 3 dans la fenêtre) : {sum(1 for c in cre.values() if c >= 3)}.")
        L.append(f"Familles (4 derniers caractères) : " + ", ".join(f"{s} {n}" for s, n in Counter(r['jeton'][-4:] for r in res).most_common(4)))
        s60 = [r["s60"] for r in res]
        L.append(f"+60 % en 120 s, multiple moyen avant frais : x{st.mean(s60):.3f} (sans les 3 meilleurs x{st.mean(sorted(s60, reverse=True)[3:]):.3f}) ; "
                 f"sur les actifs seulement (biais du futur, pour info) : x{st.mean([r['s60'] for r in act]) if act else 0:.3f}")
        L.append(f"Achat du créateur dans la tx de création : médiane {st.median([r['dev_achat'] for r in res]):.0f} $ ; "
                 f"chez les x5 : médiane {st.median([r['dev_achat'] for r in x5]) if x5 else 0:.0f} $")
        L.append(f"Transactions dans les blocs 0 à +2 : médiane {st.median([r['tx_blocs_0_2'] for r in res]):.0f} ; chez les x5 : "
                 f"{st.median([r['tx_blocs_0_2'] for r in x5]) if x5 else 0:.0f}")
        fp = [r["frais_pct"] for r in res if r["frais_pct"] is not None]
        if fp:
            L.append(f"Frais lus dans les événements (médiane) : {st.median(fp):.2f} % par trade")
    print(ecrire_txt(f"{a.nom}.txt", L))


if __name__ == "__main__":
    main()
