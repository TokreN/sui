"""H9b : acheter à la migration Flap -> pool DEX, sur un GROS échantillon (une fenêtre de création au choix).

1) Lit tous les TokenCreated du Portal Flap dans la fenêtre (peu de données : pas les trades de la courbe).
2) Portal.getTokenV8Safe(token) : taxe achat (mot 12), taxe vente (mot 13), pool DEX (mot 14), dexId (mot 17).
3) Pools migrés : logs Mint / Sync / Swap (V2). Migration = 1er Mint ; entrée = réserves à la fin du bloc +2.
4) Sorties : +60 %/120 s, +100 %/600 s, stop suiveur 30 % (sinon prix à 24 h), garder 1 h, garder 24 h.
   Plus hauts sur swaps >= 5 $ seulement. Temps estimé à 0,45 s par bloc (BSC).
5) Net = brut x (1 - 0,25 % - taxe achat) x (1 - 0,25 % - taxe vente).

Usage : RPC_URL=https://bsc-rpc.publicnode.com python migrations_flap2.py --debut 2026-10-30T00:00 --fin 2026-10-31T00:00 --prix-natif 706 --nom mig_etude
Sorties : <nom>.txt ; cache/<nom>.json (une ligne par migration).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
import sys
import urllib.request
from collections import Counter

from commun import CACHE_DIR, ecrire_txt, en_parallele, rpc, sujet
from exits_flap import CREE, PORTAL, SELV8, bloc_a, h2i, logs, ts_bloc

WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
MINT = sujet("Mint(address,uint256,uint256)")
SYNC = sujet("Sync(uint112,uint112)")
SWAP = sujet("Swap(address,uint256,uint256,uint256,uint256,address)")
SORTIES = ("F_60_120s", "F_100_600s", "T_trail30", "H_1h", "H_24h")
S_BLOC = 0.45


def w(d, i):
    return int(d[2 + 64 * i: 2 + 64 * (i + 1)], 16)


def etats(jetons, fils=3):
    def un(lot):
        corps = [{"jsonrpc": "2.0", "id": i, "method": "eth_call",
                  "params": [{"to": PORTAL, "data": SELV8 + "0" * 24 + t[2:]}, "latest"]} for i, t in enumerate(lot)]
        req = urllib.request.Request(os.environ["RPC_URL"], data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "filon1"})
        for _ in range(5):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    rep = json.loads(r.read())
                o = {}
                for x in rep if isinstance(rep, list) else []:
                    d = x.get("result")
                    if d and len(d) >= 2 + 64 * 18:
                        pool = "0x" + d[2 + 64 * 14 + 24: 2 + 64 * 15]
                        o[lot[x["id"]]] = (w(d, 12), w(d, 13), pool if int(pool, 16) else None, w(d, 17))
                return o
            except Exception:
                import time
                time.sleep(3)
        return {}
    res = {}
    for o in en_parallele(un, [jetons[i:i + 25] for i in range(0, len(jetons), 25)], fils=fils):
        res.update(o)
    return res


def logs_coupes(filtre, de, a):
    try:
        return rpc("eth_getLogs", [{**filtre, "fromBlock": hex(de), "toBlock": hex(a)}], essais=3)
    except Exception:
        if a - de < 10:
            raise
        m = (de + a) // 2
        return logs_coupes(filtre, de, m) + logs_coupes(filtre, m + 1, a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debut", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--prix-natif", type=float, required=True)
    ap.add_argument("--nom", required=True)
    ap.add_argument("--pas", type=int, default=3000)
    a = ap.parse_args()
    t0 = int(dt.datetime.fromisoformat(a.debut).replace(tzinfo=dt.UTC).timestamp())
    t1 = int(dt.datetime.fromisoformat(a.fin).replace(tzinfo=dt.UTC).timestamp())
    tete = h2i(rpc("eth_blockNumber", []))
    b0, b1 = bloc_a(t0, tete), bloc_a(t1, tete)
    if not rpc("eth_getLogs", [{"address": "0x55d398326f99059fF775485246999027B3197955", "fromBlock": hex(b0), "toBlock": hex(b0 + 20)}]):
        raise SystemExit(f"TROU DE DONNÉES au bloc {b0}.")
    crees = {}
    for l in logs([CREE], b0, b1 - 1, 9999, 6):
        d = l["data"]
        crees["0x" + d[2 + 64 * 3 + 24: 2 + 64 * 4]] = h2i(l["blockNumber"])
    print(f"jetons créés : {len(crees)}", file=sys.stderr)
    et = etats(list(crees))
    mig = {t: v for t, v in et.items() if v[2]}
    print(f"états lus : {len(et)} ; migrés : {len(mig)}", file=sys.stderr)
    adrs = sorted({v[2] for v in mig.values()})
    bmin = min(crees[t] for t in mig) if mig else b0
    ev = {}
    for i in range(0, len(adrs), 10):
        lot = adrs[i:i + 10]
        tr = [(x, min(x + a.pas - 1, tete)) for x in range(bmin, tete + 1, a.pas)]
        for r in en_parallele(lambda t, lot=lot: logs_coupes({"address": lot, "topics": [[MINT, SYNC, SWAP]]}, t[0], t[1]), tr, fils=6):
            for l in r:
                ev.setdefault(l["address"].lower(), []).append((h2i(l["blockNumber"]), h2i(l["logIndex"]), l["topics"][0], l["data"]))
        print(f"  logs lus pour {min(i + 10, len(adrs))}/{len(adrs)} pools", file=sys.stderr)
    recs = []
    sans_mint = 0
    for tok, (ta, tv, pool, dex) in mig.items():
        evs = sorted(ev.get(pool.lower(), []))
        mints = [e for e in evs if e[2] == MINT]
        if not mints:
            sans_mint += 1
            continue
        m = mints[0][0]
        tok0 = int(tok, 16) < int(WBNB, 16)

        def prix(d):
            r0, r1 = w(d, 0), w(d, 1)
            rt, rq = (r0, r1) if tok0 else (r1, r0)
            return rq / rt if rt else 0
        syncs = {(b, li): d for b, li, top, d in evs if top == SYNC}
        e = None
        for b, li, top, d in evs:
            if top == SYNC and b <= m + 2:
                e = prix(d)
        if not e:
            continue
        p120 = p600 = p1h = p24 = e
        hit60 = hit100 = None
        peak = e
        trail = None
        couvre24 = (tete - (m + 2)) * S_BLOC >= 86400
        for b, li, top, d in evs:
            if b <= m + 2:
                continue
            dts = (b - (m + 2)) * S_BLOC
            if top == SYNC:
                x = prix(d)
                if dts <= 120:
                    p120 = x
                if dts <= 600:
                    p600 = x
                if dts <= 3600:
                    p1h = x
                if dts <= 86400:
                    p24 = x
            elif top == SWAP:
                s = syncs.get((b, li - 1))
                if not s:
                    continue
                x = prix(s)
                q = (w(d, 1) + w(d, 3)) if tok0 else (w(d, 0) + w(d, 2))
                if q / 1e18 * a.prix_natif < 5:
                    continue
                if dts <= 120 and hit60 is None and x >= 1.6 * e:
                    hit60 = True
                if dts <= 600 and hit100 is None and x >= 2 * e:
                    hit100 = True
                if dts <= 86400:
                    peak = max(peak, x)
                    if trail is None and peak > e and x <= 0.7 * peak:
                        trail = x
        fac = (1 - 0.0025 - ta / 1e4) * (1 - 0.0025 - tv / 1e4)
        brut = {"F_60_120s": 1.6 if hit60 else p120 / e, "F_100_600s": 2.0 if hit100 else p600 / e,
                "T_trail30": (trail if trail is not None else p24) / e, "H_1h": p1h / e, "H_24h": p24 / e}
        recs.append({"jeton": tok, "pool": pool, "dex": dex, "taxe": [ta, tv], "delai_blocs": m - crees[tok],
                     "couvre24": couvre24, "net": {k: min(v * fac, 1e4) for k, v in brut.items()}})
    with open(os.path.join(CACHE_DIR, f"{a.nom}.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f)
    L = [f"{a.nom} : jetons créés {a.debut} -> {a.fin} UTC : {len(crees)} ; migrés : {len(mig)} ({100 * len(mig) / max(len(crees), 1):.1f} %) ; "
         f"mesurés (pool V2 avec Mint) : {len(recs)} ; sans Mint V2 : {sans_mint}.",
         "dexId des migrés : " + ", ".join(f"{k} {n}" for k, n in Counter(v[3] for v in mig.values()).most_common()),
         "Taxes des mesurés (achat, vente) : " + ", ".join(f"{k} {n}" for k, n in Counter(tuple(r['taxe']) for r in recs).most_common(4))]
    if recs:
        dl = sorted(r["delai_blocs"] * S_BLOC / 60 for r in recs)
        L.append(f"Délai création -> migration : médiane {st.median(dl):.0f} min (p10 {dl[len(dl) // 10]:.0f}, p90 {dl[9 * len(dl) // 10]:.0f}).")
        for s in SORTIES:
            pool_s = [r for r in recs if s != "H_24h" or r["couvre24"]]
            nets = sorted((r["net"][s] for r in pool_s), reverse=True)
            if nets:
                L.append(f"   {s:<11} n={len(nets)} net moyen x{st.mean(nets):.3f} | sans top3 x{st.mean(nets[3:]) if len(nets) > 3 else 0:.3f} | "
                         f"médiane x{st.median(nets):.3f} | part > 1 : {sum(1 for x in nets if x > 1)} sur {len(nets)}")
    print(ecrire_txt(f"{a.nom}.txt", L))


if __name__ == "__main__":
    main()
