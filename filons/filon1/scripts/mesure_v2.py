"""Mesure d'une usine Uniswap V2 (ou fork) : tous les pairs créés, prix par Sync, retraits de LP par Burn.

RPC : variable d'environnement RPC_URL. Aucune clé.
Exemple (HyperSwap V2 sur HyperEVM, pairs nés du 23 au 31/10/2026, suivi 24 h, HYPE à 88 $) :
  RPC_URL=https://rpc.hyperliquid.xyz/evm python mesure_v2.py --usine 0x724412c00059bf7d6ee7d4a1d0d5cd4de3ea1c48 \
     --quote 0x5555555555555555555555555555555555555555:88:18 --debut 2026-10-23T00:00 --fin 2026-10-31T00:00 \
     --suivi 24 --pas 1000 --nom hyperswap_v2

Définitions : celles de mesure_v4.py. Bloc de référence = premier bloc avec de la liquidité (Mint), entrée = fin du bloc +2.
Retrait de LP = un Burn qui retire >= 50 % de la réserve en devise de cotation.
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
from mesure_v4 import bloc_a, ts_bloc, txs

PAIR = sujet("PairCreated(address,address,address,uint256)")
SWAP = sujet("Swap(address,uint256,uint256,uint256,uint256,address)")
SYNC = sujet("Sync(uint112,uint112)")
BURN = sujet("Burn(address,uint256,uint256,address)")
MINT = sujet("Mint(address,uint256,uint256)")


def h2i(x):
    return int(x, 16)


def mot(d, i):
    return int(d[2 + 64 * i: 2 + 64 * (i + 1)], 16)


def plages(de, a, pas):
    return [(x, min(x + pas - 1, a)) for x in range(de, a + 1, pas)]


def logs_surs(filtre, de, a):
    """eth_getLogs sur [de, a] ; coupe la plage en deux si le RPC échoue (délai, taille)."""
    try:
        return rpc("eth_getLogs", [{**filtre, "fromBlock": hex(de), "toBlock": hex(a)}], essais=4)
    except Exception:
        if a - de < 20:
            raise
        m = (de + a) // 2
        return logs_surs(filtre, de, m) + logs_surs(filtre, m + 1, a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--usine", required=True)
    ap.add_argument("--quote", required=True, help="adresse:prix_usd:decimales[,...]")
    ap.add_argument("--debut", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--suivi", type=float, default=24)
    ap.add_argument("--pas", type=int, default=1000)
    ap.add_argument("--fils", type=int, default=8)
    ap.add_argument("--pairs-par-appel", type=int, default=50)
    ap.add_argument("--nom", required=True)
    a = ap.parse_args()
    quotes = {q.split(":")[0].lower(): (float(q.split(":")[1]), int(q.split(":")[2])) for q in a.quote.split(",")}

    t0 = int(dt.datetime.fromisoformat(a.debut).replace(tzinfo=dt.UTC).timestamp())
    t1 = int(dt.datetime.fromisoformat(a.fin).replace(tzinfo=dt.UTC).timestamp())
    t2 = t1 + int(a.suivi * 3600)
    tete = h2i(rpc("eth_blockNumber", []))
    b0, b1 = bloc_a(t0, tete), bloc_a(t1, tete)
    b2 = bloc_a(t2, tete) if t2 < ts_bloc(tete) else tete
    print(f"blocs {b0} -> {b1}, suivi -> {b2}", file=sys.stderr)

    def un(t):
        return logs_surs({"address": a.usine, "topics": [PAIR]}, t[0], t[1])

    pairs = {}
    n_pairs = 0
    for r in en_parallele(un, plages(b0, b1 - 1, a.pas), fils=a.fils):
        for l in r:
            n_pairs += 1
            t0_, t1_ = "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:]
            if t0_ in quotes:
                cote = 0
            elif t1_ in quotes:
                cote = 1
            else:
                continue
            adr = "0x" + l["data"][2 + 24: 2 + 64]
            pairs[adr] = {"pair": adr, "jeton": t1_ if cote == 0 else t0_, "q": t0_ if cote == 0 else t1_, "cote": cote,
                          "bloc_pair": h2i(l["blockNumber"]), "tx": l["transactionHash"], "ev": []}
    print(f"pairs créés : {n_pairs} ; cotés : {len(pairs)}", file=sys.stderr)

    adrs = list(pairs)
    for i in range(0, len(adrs), a.pairs_par_appel):
        lot = adrs[i: i + a.pairs_par_appel]

        def ev(t, lot=lot):
            return logs_surs({"address": lot, "topics": [[SWAP, SYNC, BURN, MINT]]}, t[0], t[1])

        for r in en_parallele(ev, plages(b0, b2, a.pas), fils=a.fils):
            for l in r:
                p = pairs.get(l["address"].lower())
                if p:
                    p["ev"].append((h2i(l["blockNumber"]), h2i(l["logIndex"]), l["topics"][0], l["data"], l["transactionHash"],
                                    h2i(l["blockTimestamp"]) if l.get("blockTimestamp") else None))
        print(f"  événements lus pour {min(i + a.pairs_par_appel, len(adrs))}/{len(adrs)} pairs", file=sys.stderr)

    tx = txs([p["tx"] for p in pairs.values()], a.fils)
    tsb0, tsb2 = ts_bloc(b0), ts_bloc(b2)

    def ts_de(b, ts):
        return ts if ts else tsb0 + (b - b0) * (tsb2 - tsb0) / max(b2 - b0, 1)

    res = []
    for p in pairs.values():
        p["ev"].sort()
        px, dec = quotes[p["q"]]
        cq = p["cote"]
        mints = [e for e in p["ev"] if e[2] == MINT]
        if not mints:
            continue
        c = mints[0][0]
        ts_c = ts_de(c, mints[0][5])
        ent = c + 2
        e = None
        rq = 0  # réserve de cotation courante
        m24 = m120 = None
        p120 = None
        t160 = t_rug = None
        ach = ven = 0.0
        na = nv = 0
        dernier = None
        tx02 = set()
        for b, li, top, d, h, tsl in p["ev"]:
            t = ts_de(b, tsl) - ts_c
            if top == SYNC:
                r0, r1 = mot(d, 0), mot(d, 1)
                rq_new, rt = (r0, r1) if cq == 0 else (r1, r0)
                prix = rq_new / rt if rt else 0
                rq = rq_new
                if b <= ent:
                    e = prix
                    m24 = m120 = p120 = dernier = prix
                    continue
                if e:
                    dernier = prix
                    if t <= 120:
                        p120 = prix
                p["_dernier_prix"] = prix
            elif top == SWAP:
                if b <= ent:
                    tx02.add(h)
                a0i, a1i, a0o, a1o = mot(d, 0), mot(d, 1), mot(d, 2), mot(d, 3)
                qin, qout = (a0i, a0o) if cq == 0 else (a1i, a1o)
                u_in, u_out = qin / 10**dec * px, qout / 10**dec * px
                if b <= ent or e is None:
                    continue
                prix = p.get("_dernier_prix", e)
                if max(u_in, u_out) < 5:
                    continue
                if t <= 120:
                    m120 = max(m120, prix)
                    if prix >= 1.6 * e and t160 is None:
                        t160 = t
                if t <= 86400:
                    m24 = max(m24, prix)
                    if u_in > u_out:
                        ach += u_in
                        na += 1
                    else:
                        ven += u_out
                        nv += 1
            elif top == BURN:
                q_out = mot(d, 0) if cq == 0 else mot(d, 1)
                if rq and q_out >= 0.5 * (rq + q_out) and t_rug is None and b > c:
                    t_rug = t
        if not e:
            continue
        if t160 is not None and (t_rug is None or t160 < t_rug):
            s60 = 1.6
        elif t_rug is not None and t_rug <= 120:
            s60 = 0.0
        else:
            s60 = p120 / e
        res.append({"pair": p["pair"], "jeton": p["jeton"], "ts": int(ts_c), "createur": tx.get(p["tx"], {}).get("from"),
                    "achats24": round(ach, 2), "ventes24": round(ven, 2), "n_ach": na, "n_ven": nv, "x24": m24 / e,
                    "s60": s60, "t_rug": t_rug, "tx_blocs_0_2": len(tx02)})

    with open(os.path.join(CACHE_DIR, f"{a.nom}_pairs.json"), "w", encoding="utf-8") as f:
        json.dump(res, f)
    L = [f"{a.nom} : usine {a.usine}, naissances {a.debut} -> {a.fin} UTC, suivi {a.suivi} h.",
         f"Pairs créés : {n_pairs} ; cotés (devise connue) : {len(pairs)} ; mesurés (avec liquidité) : {len(res)}."]
    if res:
        jour = defaultdict(list)
        for r in res:
            jour[dt.datetime.fromtimestamp(r["ts"], dt.UTC).strftime("%Y-%m-%d")].append(r)
        L.append("jour | pairs | actifs (>=220 $ achetés 24 h) | créateurs des actifs | x5 24 h (>=2 200 $) | achats 24 h | LP retirée < 24 h")
        for j in sorted(jour):
            rs = jour[j]
            act = [r for r in rs if r["achats24"] >= 220]
            x5 = [r for r in rs if 5 <= r["x24"] <= 10000 and r["achats24"] >= 2200]
            L.append(f"{j} | {len(rs)} | {len(act)} | {len({r['createur'] for r in act})} | {len(x5)} | {sum(r['achats24'] for r in rs):,.0f} $ | "
                     f"{sum(1 for r in rs if r['t_rug'] is not None and r['t_rug'] < 86400)}")
        cre = Counter(r["createur"] for r in res)
        L.append(f"Créateurs : {len(cre)} ; en série (>= 3) : {sum(1 for n in cre.values() if n >= 3)}.")
        rug = [r["t_rug"] for r in res if r["t_rug"] is not None]
        L.append(f"Retrait de LP : {len(rug)} sur {len(res)}" + (f" ; délai médian {st.median(rug) / 60:.0f} min" if rug else ""))
        s60 = [r["s60"] for r in res]
        L.append(f"+60 % en 120 s (retrait = -100 %), multiple moyen avant frais : x{st.mean(s60):.3f}"
                 + (f" ; sans les 3 meilleurs x{st.mean(sorted(s60, reverse=True)[3:]):.3f}" if len(s60) > 3 else ""))
        x5 = [r for r in res if 5 <= r["x24"] <= 10000 and r["achats24"] >= 2200]
        L.append(f"x5 : {len(x5)} ; dont LP retirée en < 24 h : {sum(1 for r in x5 if r['t_rug'] is not None and r['t_rug'] < 86400)}")
        L.append(f"Ventes bloquées probables (>= 5 achats, 0 vente) : {sum(1 for r in res if r['n_ach'] >= 5 and r['n_ven'] == 0)} sur {len(res)}")
        L.append(f"Tx de swap dans les blocs 0 à +2 (médiane) : {st.median([r['tx_blocs_0_2'] for r in res]):.0f}")
    print(ecrire_txt(f"{a.nom}.txt", L))


if __name__ == "__main__":
    main()
