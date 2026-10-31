"""Teste un MENU de règles de sortie a priori, croisé avec des SÉLECTIONS observables à l'entrée,
sur Flap.sh (BSC), et compare deux fenêtres indépendantes (test hors-échantillon simple).

But : savoir s'il existe une case (sélection x sortie) rentable net de taxes, robuste d'une fenêtre à l'autre
ET sans les 3 meilleurs jetons. Tout est décidé AVANT de regarder les résultats (voir JOURNAL.md).

Usage :
  RPC_URL=https://bsc-rpc.publicnode.com python exits_flap.py --prix-natif 706 \
     --fenetres 2026-10-30T12:00/2026-10-30T15:00 2026-10-29T18:00/2026-10-29T21:00 --suivi 24

Prix (postPrice dans l'événement) = prix sur la courbe, en unités de cotation. Entrée = fin du bloc +2.
Net = multiple brut x (1 - 0,01 - taxe_achat) x (1 - 0,01 - taxe_vente). Gaz (~0,0035 $) négligé.
Taxe lue sur le Portal (getTokenV8Safe) au bloc latest. Sur la courbe, pas de retrait de LP : le prix reflète les ventes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
import sys
from collections import Counter, defaultdict

from commun import CACHE_DIR, ecrire_txt, en_parallele, keccak256, rpc, sujet
from mesure_v4 import txs

PORTAL = "0xe2cE6ab80874Fa9Fa2aAE65D277Dd6B8e65C9De0"
CREE = sujet("TokenCreated(uint256,address,uint256,address,string,string,string)")
ACHAT = sujet("TokenBought(uint256,address,address,uint256,uint256,uint256,uint256)")
VENTE = sujet("TokenSold(uint256,address,address,uint256,uint256,uint256,uint256)")
SELV8 = "0x" + keccak256(b"getTokenV8Safe(address)").hex()[:8]
DOLLARS = {"0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d": 1.0,
           "0x55d398326f99059ff775485246999027b3197955": 1.0,
           "0x0782b6d8c4551b9760e74c0545a9bcd90bdc41e5": 1.0}


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


def logs(topics, de, a, pas, fils):
    tr = [(x, min(x + pas - 1, a)) for x in range(de, a + 1, pas)]
    out = []
    for r in en_parallele(lambda t: rpc("eth_getLogs", [{"address": PORTAL, "fromBlock": hex(t[0]), "toBlock": hex(t[1]), "topics": topics}]), tr, fils=fils):
        out.extend(r)
    return out


def taxes(jetons, fils):
    def un(lot):
        import urllib.request
        corps = [{"jsonrpc": "2.0", "id": i, "method": "eth_call", "params": [{"to": PORTAL, "data": SELV8 + "0" * 24 + t[2:]}, "latest"]} for i, t in enumerate(lot)]
        req = urllib.request.Request(os.environ["RPC_URL"], data=json.dumps(corps).encode(), headers={"Content-Type": "application/json", "User-Agent": "filon1"})
        for _ in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    rep = json.loads(r.read())
                o = {}
                for x in rep if isinstance(rep, list) else []:
                    d = x.get("result")
                    if d and len(d) >= 2 + 64 * 14:
                        o[lot[x["id"]]] = (mot(d, 12), mot(d, 13))
                return o
            except Exception:
                import time
                time.sleep(2)
        return {}
    res = {}
    for o in en_parallele(un, [jetons[i:i + 25] for i in range(0, len(jetons), 25)], fils=fils):
        res.update(o)
    return res


def mesurer_fenetre(deb, fin, suivi, px_natif, pas, fils):
    t0 = int(dt.datetime.fromisoformat(deb).replace(tzinfo=dt.UTC).timestamp())
    t1 = int(dt.datetime.fromisoformat(fin).replace(tzinfo=dt.UTC).timestamp())
    t2 = t1 + int(suivi * 3600)
    tete = h2i(rpc("eth_blockNumber", []))
    b0, b1, b2 = bloc_a(t0, tete), bloc_a(t1, tete), min(bloc_a(t2, tete), tete)
    # contrôle positif : le RPC sert-il ces blocs ?
    if not rpc("eth_getLogs", [{"address": "0x55d398326f99059fF775485246999027B3197955", "fromBlock": hex(b0), "toBlock": hex(b0 + 20)}]):
        raise SystemExit(f"TROU DE DONNÉES au bloc {b0} : RPC ne sert pas ces blocs.")
    jetons = {}
    for l in logs([CREE], b0, b1 - 1, pas, fils):
        d = l["data"]
        tok = "0x" + d[2 + 64 * 3 + 24: 2 + 64 * 4]
        jetons[tok] = {"jeton": tok, "createur": "0x" + d[2 + 64 + 24: 2 + 128], "ts": mot(d, 0),
                       "bloc": h2i(l["blockNumber"]), "tx": l["transactionHash"], "cote": "0x" + "0" * 40, "trades": []}
    for l in logs([sujet("TokenQuoteSet(address,address)")], b0, b1 - 1, pas, fils):
        d = l["data"]
        tok = "0x" + d[2 + 24: 2 + 64]
        if tok in jetons:
            jetons[tok]["cote"] = "0x" + d[2 + 64 + 24: 2 + 128]
    for sens, top in ((1, ACHAT), (-1, VENTE)):
        for l in logs([top], b0, b2, pas, fils):
            d = l["data"]
            tok = "0x" + d[2 + 64 + 24: 2 + 128]
            j = jetons.get(tok)
            if j:
                j["trades"].append((h2i(l["blockNumber"]), h2i(l["logIndex"]), mot(d, 0), sens, mot(d, 4), mot(d, 6), l["transactionHash"]))
    tax = taxes(list(jetons), fils)
    # créateur « nouveau » = aucun jeton créé plus tôt dans la fenêtre
    vu = defaultdict(int)
    recs = []
    for j in sorted(jetons.values(), key=lambda j: (j["ts"], j["bloc"])):
        q = j["cote"]
        px = px_natif if q == "0x" + "0" * 40 else DOLLARS.get(q)
        nouveau = vu[j["createur"]] == 0
        vu[j["createur"]] += 1
        if px is None:
            continue
        tr = sorted(j["trades"])
        ent = j["bloc"] + 2
        e = None
        for t in tr:
            if t[0] <= ent:
                e = t[5]
        if e is None:
            e = tr[0][5] if tr else None
        if not e:
            continue
        dev = sum(t[4] for t in tr if t[6] == j["tx"] and t[3] == 1) / 1e18 * px
        tx02 = len({t[6] for t in tr if t[0] <= ent})
        # chemin de prix après l'entrée
        peak = e
        exits = {}
        p120 = px1h = px6h = px24 = e
        hit60 = hit100 = None
        t30 = t50 = None
        for t in tr:
            if t[0] <= ent:
                continue
            dtc = t[2] - j["ts"]
            x = t[5]
            u = t[4] / 1e18 * px
            if u < 5 and t[3] == 1:
                pass  # poussière à l'achat ignorée pour les plus hauts, mais le prix reste
            if dtc <= 120:
                p120 = x
                if x >= 1.6 * e and hit60 is None:
                    hit60 = x
            if dtc <= 600 and x >= 2 * e and hit100 is None:
                hit100 = x
            if dtc <= 3600:
                px1h = x
            if dtc <= 21600:
                px6h = x
            if dtc <= 86400:
                px24 = x
            if x > peak:
                peak = x
            if t30 is None and peak > e and x <= 0.7 * peak and dtc <= 86400:
                t30 = x
            if t50 is None and peak > e and x <= 0.5 * peak and dtc <= 86400:
                t50 = x
        exits["F_60_120s"] = (1.6 if hit60 else p120 / e)
        exits["F_100_600s"] = (2.0 if hit100 else (p120 / e))
        exits["H_1h"] = px1h / e
        exits["H_6h"] = px6h / e
        exits["H_24h"] = px24 / e
        exits["T_trail30"] = (t30 / e) if t30 is not None else px24 / e
        exits["T_trail50"] = (t50 / e) if t50 is not None else px24 / e
        bt, stx = tax.get(j["jeton"], (900, 900))  # défaut prudent 9 % si non lu
        recs.append({"jeton": j["jeton"], "nouveau": nouveau, "taxe_a": bt, "taxe_v": stx, "dev": dev,
                     "tx02": tx02, "achats24": sum(t[4] / 1e18 * px for t in tr if t[3] == 1 and t[0] > ent and t[2] - j["ts"] <= 86400),
                     "exits": exits})
    return recs


def menu(recs, label):
    L = [f"== {label} : {len(recs)} jetons cotés mesurés =="]
    selections = {
        "tous": lambda r: True,
        "actif>=220$": lambda r: r["achats24"] >= 220,
        "nouveau créateur": lambda r: r["nouveau"],
        "taxe<=1%": lambda r: r["taxe_a"] <= 100 and r["taxe_v"] <= 100,
        "nouveau ET taxe<=1%": lambda r: r["nouveau"] and r["taxe_a"] <= 100 and r["taxe_v"] <= 100,
        "nouveau ET dev=0": lambda r: r["nouveau"] and r["dev"] < 5,
    }
    reglems = ["F_60_120s", "F_100_600s", "H_1h", "H_6h", "H_24h", "T_trail30", "T_trail50"]
    for snom, sf in selections.items():
        sub = [r for r in recs if sf(r)]
        if not sub:
            L.append(f"  [{snom}] n=0")
            continue
        L.append(f"  [{snom}] n={len(sub)}")
        for rg in reglems:
            nets = sorted((r["exits"][rg] * (1 - 0.01 - r["taxe_a"] / 1e4) * (1 - 0.01 - r["taxe_v"] / 1e4) for r in sub), reverse=True)
            nets = [min(x, 1e4) for x in nets]
            moy = st.mean(nets)
            sans3 = st.mean(nets[3:]) if len(nets) > 3 else 0.0
            gagn = sum(1 for x in nets if x > 1) / len(nets)
            L.append(f"      {rg:<12} net moyen x{moy:.3f} | sans top3 x{sans3:.3f} | part >1 {gagn:.0%}")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fenetres", nargs="+", required=True, help="deb/fin en UTC, ex. 2026-10-30T12:00/2026-10-30T15:00")
    ap.add_argument("--suivi", type=float, default=24)
    ap.add_argument("--prix-natif", type=float, required=True)
    ap.add_argument("--pas", type=int, default=9999)
    ap.add_argument("--fils", type=int, default=6)
    a = ap.parse_args()
    out = ["Menu de sorties x sélections, Flap.sh, net de taxes (défaut 9 % si non lu). Décidé avant de compter."]
    tous = {}
    for f in a.fenetres:
        deb, fin = f.split("/")
        recs = mesurer_fenetre(deb, fin, a.suivi, a.prix_natif, a.pas, a.fils)
        tous[f] = recs
        out += menu(recs, f)
        print(f"fenêtre {f} : {len(recs)} jetons", file=sys.stderr)
    # test hors-échantillon : une case doit tenir (>1 net, sans top3) sur TOUTES les fenêtres
    out.append("== Lecture : une piste n'est retenue que si 'sans top3' > 1 sur CHAQUE fenêtre ==")
    with open(os.path.join(CACHE_DIR, "exits_flap.json"), "w", encoding="utf-8") as fch:
        json.dump({k: [{kk: vv for kk, vv in r.items()} for r in v] for k, v in tous.items()}, fch)
    print(ecrire_txt("exits_flap.txt", out))


if __name__ == "__main__":
    main()
