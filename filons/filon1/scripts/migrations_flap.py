"""Hypothèse H9 : acheter au moment où un jeton Flap migre de la courbe vers son pool DEX (V2), sans info du futur.

Univers : TOUS les jetons des fenêtres déjà lues par momentum_flap.py (cache/momentum_*.json).
1) Portal.getTokenV8Safe(token) -> mot 14 = pool DEX (0 = pas migré).
2) Logs du pool (Mint / Sync / Swap). Migration = 1er Mint. Entrée = réserves à la fin du bloc de migration + 2.
3) Sorties : +60 %/120 s, +100 %/600 s, stop suiveur 30 % (sinon prix à 24 h), garder 1 h, garder 24 h.
   Plus hauts calculés seulement sur des swaps >= 5 $ (poussière ignorée). Temps estimé à 0,45 s par bloc BSC.
4) Net = brut x (1 - 0,25 % - taxe achat) x (1 - 0,25 % - taxe vente) (frais PancakeSwap V2 0,25 %).

Usage : RPC_URL=https://bsc-rpc.publicnode.com python migrations_flap.py --prix-natif 706
Sortie : migrations_flap.txt
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
import urllib.request

from commun import CACHE_DIR, ecrire_txt, en_parallele, rpc, sujet
from exits_flap import PORTAL, SELV8

WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
MINT = sujet("Mint(address,uint256,uint256)")
SYNC = sujet("Sync(uint112,uint112)")
SWAP = sujet("Swap(address,uint256,uint256,uint256,uint256,address)")
SORTIES = ("F_60_120s", "F_100_600s", "T_trail30", "H_1h", "H_24h")
S_BLOC = 0.45


def w(d, i):
    return int(d[2 + 64 * i: 2 + 64 * (i + 1)], 16)


def logs_coupes(filtre, de, a):
    """eth_getLogs ; coupe la plage en deux si le RPC refuse (trop de résultats)."""
    try:
        return rpc("eth_getLogs", [{**filtre, "fromBlock": hex(de), "toBlock": hex(a)}], essais=3)
    except Exception:
        if a - de < 10:
            raise
        m = (de + a) // 2
        return logs_coupes(filtre, de, m) + logs_coupes(filtre, m + 1, a)


def pools_de(jetons, fils=3):
    def un(lot):
        corps = [{"jsonrpc": "2.0", "id": i, "method": "eth_call",
                  "params": [{"to": PORTAL, "data": SELV8 + "0" * 24 + t[2:]}, "latest"]} for i, t in enumerate(lot)]
        req = urllib.request.Request(os.environ["RPC_URL"], data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "filon1"})
        for _ in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    rep = json.loads(r.read())
                o = {}
                for x in rep if isinstance(rep, list) else []:
                    d = x.get("result")
                    if d and len(d) >= 2 + 64 * 16:
                        pool = "0x" + d[2 + 64 * 14 + 24: 2 + 64 * 15]
                        o[lot[x["id"]]] = pool if int(pool, 16) else None
                return o
            except Exception:
                import time
                time.sleep(2)
        return {}
    res = {}
    for o in en_parallele(un, [jetons[i:i + 25] for i in range(0, len(jetons), 25)], fils=fils):
        res.update(o)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prix-natif", type=float, required=True)
    ap.add_argument("--pas", type=int, default=3000)
    a = ap.parse_args()
    tete = int(rpc("eth_blockNumber", []), 16)
    L = ["H9 migrations Flap -> pool DEX V2 ; net de frais 0,25 % x 2 et taxes lues ; poussière < 5 $ ignorée pour les plus hauts."]
    toutes = []
    for f in sorted(glob.glob(os.path.join(CACHE_DIR, "momentum_*.json"))):
        jetons = json.load(open(f))
        pools = pools_de(list(jetons))
        mig = {t: p for t, p in pools.items() if p}
        nom = os.path.basename(f)
        if not mig:
            L.append(f"{nom} : {len(jetons)} jetons, 0 migration.")
            continue
        b0 = min(jetons[t]["bloc"] for t in mig)
        adrs = list(set(mig.values()))
        ev = []
        for i in range(0, len(adrs), 10):
            lot = adrs[i:i + 10]
            tr = [(x, min(x + a.pas - 1, tete)) for x in range(b0, tete + 1, a.pas)]
            for r in en_parallele(lambda t, lot=lot: logs_coupes({"address": lot, "topics": [[MINT, SYNC, SWAP]]}, t[0], t[1]), tr, fils=6):
                ev.extend(r)
        par_pool = {}
        for l in ev:
            par_pool.setdefault(l["address"].lower(), []).append((int(l["blockNumber"], 16), int(l["logIndex"], 16), l["topics"][0], l["data"]))
        n_ok = 0
        for tok, pool in mig.items():
            evs = sorted(par_pool.get(pool.lower(), []))
            mints = [e for e in evs if e[2] == MINT]
            if not mints:
                continue
            m = mints[0][0]
            tok_est0 = int(tok, 16) < int(WBNB, 16)  # token0 = adresse la plus petite
            def prix(d):
                r0, r1 = w(d, 0), w(d, 1)
                rt, rq = (r0, r1) if tok_est0 else (r1, r0)
                return rq / rt if rt else 0
            e = None
            syncs = {(b, li): d for b, li, top, d in evs if top == SYNC}
            for b, li, top, d in evs:
                if top == SYNC and b <= m + 2:
                    e = prix(d)
            if not e:
                continue
            p120 = p600 = p1h = p24 = e
            hit60 = hit100 = None
            peak = e
            trail = None
            for b, li, top, d in evs:
                if b <= m + 2:
                    continue
                dt_s = (b - (m + 2)) * S_BLOC
                if top == SYNC:
                    x = prix(d)
                    if dt_s <= 120:
                        p120 = x
                    if dt_s <= 600:
                        p600 = x
                    if dt_s <= 3600:
                        p1h = x
                    if dt_s <= 86400:
                        p24 = x
                elif top == SWAP:
                    s = syncs.get((b, li - 1))
                    if not s:
                        continue
                    x = prix(s)
                    a0i, a1i, a0o, a1o = w(d, 0), w(d, 1), w(d, 2), w(d, 3)
                    q = (a1i + a1o) if tok_est0 else (a0i + a0o)
                    if q / 1e18 * a.prix_natif < 5:
                        continue
                    if dt_s <= 120 and hit60 is None and x >= 1.6 * e:
                        hit60 = True
                    if dt_s <= 600 and hit100 is None and x >= 2 * e:
                        hit100 = True
                    if dt_s <= 86400:
                        peak = max(peak, x)
                        if trail is None and peak > e and x <= 0.7 * peak:
                            trail = x
            ta, tv = jetons[tok].get("taxe", [900, 900])
            fac = (1 - 0.0025 - ta / 1e4) * (1 - 0.0025 - tv / 1e4)
            brut = {"F_60_120s": 1.6 if hit60 else p120 / e, "F_100_600s": 2.0 if hit100 else p600 / e,
                    "T_trail30": (trail if trail is not None else p24) / e, "H_1h": p1h / e, "H_24h": p24 / e}
            toutes.append((nom, {k: min(v * fac, 1e4) for k, v in brut.items()}))
            n_ok += 1
        L.append(f"{nom} : {len(jetons)} jetons, {len(mig)} migrés, {n_ok} mesurés (pool avec liquidité).")
        for s in SORTIES:
            nets = sorted((r[s] for n, r in toutes if n == nom), reverse=True)
            if nets:
                L.append(f"   {s:<11} n={len(nets)} net moyen x{st.mean(nets):.3f} | sans top3 x{st.mean(nets[3:]) if len(nets) > 3 else 0:.3f} | part > 1 : {sum(1 for x in nets if x > 1)} sur {len(nets)}")
    L.append("Deux fenêtres réunies :")
    for s in SORTIES:
        nets = sorted((r[s] for _, r in toutes), reverse=True)
        if nets:
            L.append(f"   {s:<11} n={len(nets)} net moyen x{st.mean(nets):.3f} | sans top3 x{st.mean(nets[3:]) if len(nets) > 3 else 0:.3f}")
    print(ecrire_txt("migrations_flap.txt", L))


if __name__ == "__main__":
    main()
