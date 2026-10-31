"""Teste « acheter seulement ceux qui décollent déjà » (momentum) sur Flap.sh, SANS information du futur.

Règle : au temps T après la création, si les achats cumulés (trades >= 5 $) atteignent Y $, on entre AU PRIX DE T.
Grille fixée d'avance (voir JOURNAL.md, hypothèse H8) : T ∈ {60, 180, 600} s ; Y ∈ {200, 1000, 3000} $ ;
sorties (temps comptés depuis l'entrée) : +60 %/120 s, +100 %/600 s, stop suiveur 30 % (sinon prix à 24 h), garder 1 h.
Net = brut x (1 - 1 % - taxe achat) x (1 - 1 % - taxe vente). Mon propre impact d'entrée n'est PAS compté (optimiste).

Usage :
  RPC_URL=https://bsc-rpc.publicnode.com python momentum_flap.py --prix-natif 706 \
     --fenetres 2026-10-30T00:00/2026-10-30T03:00 2026-10-30T12:00/2026-10-30T15:00 --suivi 24
Sorties : momentum_flap.txt ; cache/momentum_<fenêtre>.json (trades bruts, pour relancer hors ligne).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
import sys

from commun import CACHE_DIR, ecrire_txt, rpc, sujet
from exits_flap import ACHAT, CREE, DOLLARS, VENTE, bloc_a, h2i, logs, mot, taxes, ts_bloc

T_LIST = (60, 180, 600)
Y_LIST = (200, 1000, 3000)
SORTIES = ("F_60_120s", "F_100_600s", "T_trail30", "H_1h")


def lire_fenetre(deb, fin, suivi, px_natif, pas, fils):
    cle = os.path.join(CACHE_DIR, f"momentum_{deb[:13].replace(':', '')}.json")
    if os.path.exists(cle):
        with open(cle, encoding="utf-8") as f:
            return json.load(f)
    t0 = int(dt.datetime.fromisoformat(deb).replace(tzinfo=dt.UTC).timestamp())
    t1 = int(dt.datetime.fromisoformat(fin).replace(tzinfo=dt.UTC).timestamp())
    t2 = t1 + int(suivi * 3600)
    tete = h2i(rpc("eth_blockNumber", []))
    b0, b1 = bloc_a(t0, tete), bloc_a(t1, tete)
    b2 = min(bloc_a(t2, tete), tete) if t2 < ts_bloc(tete) else tete
    if not rpc("eth_getLogs", [{"address": "0x55d398326f99059fF775485246999027B3197955", "fromBlock": hex(b0), "toBlock": hex(b0 + 20)}]):
        raise SystemExit(f"TROU DE DONNÉES au bloc {b0} : le RPC ne sert pas ces blocs.")
    jetons = {}
    for l in logs([CREE], b0, b1 - 1, pas, fils):
        d = l["data"]
        tok = "0x" + d[2 + 64 * 3 + 24: 2 + 64 * 4]
        jetons[tok] = {"ts": mot(d, 0), "bloc": h2i(l["blockNumber"]), "cote": "0x" + "0" * 40, "tr": []}
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
                q = j["cote"]
                px = px_natif if q == "0x" + "0" * 40 else DOLLARS.get(q)
                if px is None:
                    continue
                j["tr"].append((h2i(l["blockNumber"]), h2i(l["logIndex"]), mot(d, 0), sens, round(mot(d, 4) / 1e18 * px, 2), mot(d, 6)))
    tx = taxes(list(jetons), fils)
    for tok, j in jetons.items():
        j["tr"].sort()
        j["taxe"] = list(tx.get(tok, (900, 900)))  # défaut prudent 9 % si non lu
    with open(cle, "w", encoding="utf-8") as f:
        json.dump(jetons, f)
    return jetons


def evaluer(j, T, Y):
    """Renvoie None si non sélectionné, sinon dict des multiples bruts par sortie."""
    tc = j["ts"]
    tr = j["tr"]
    vol = 0.0
    e = None
    i0 = None
    for i, t in enumerate(tr):
        if t[2] > tc + T:
            break
        if t[3] == 1 and t[4] >= 5:
            vol += t[4]
        e, i0 = t[5], i
    if vol < Y or not e:
        return None
    te = tc + T
    apres = tr[i0 + 1:]
    p120 = p600 = p1h = p24 = e
    hit60 = hit100 = None
    peak = e
    trail = None
    for t in apres:
        dtt = t[2] - te
        x = t[5]
        if dtt <= 120:
            p120 = x
        if dtt <= 600:
            p600 = x
        if dtt <= 3600:
            p1h = x
        if dtt <= 86400:
            p24 = x
        if t[4] < 5:
            continue
        if dtt <= 120 and hit60 is None and x >= 1.6 * e:
            hit60 = True
        if dtt <= 600 and hit100 is None and x >= 2 * e:
            hit100 = True
        if dtt <= 86400:
            peak = max(peak, x)
            if trail is None and peak > e and x <= 0.7 * peak:
                trail = x
    return {"F_60_120s": 1.6 if hit60 else p120 / e, "F_100_600s": 2.0 if hit100 else p600 / e,
            "T_trail30": (trail if trail is not None else p24) / e, "H_1h": p1h / e}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fenetres", nargs="+", required=True)
    ap.add_argument("--suivi", type=float, default=24)
    ap.add_argument("--prix-natif", type=float, required=True)
    ap.add_argument("--pas", type=int, default=9999)
    ap.add_argument("--fils", type=int, default=6)
    a = ap.parse_args()
    data = {}
    for f in a.fenetres:
        deb, fin = f.split("/")
        data[f] = lire_fenetre(deb, fin, a.suivi, a.prix_natif, a.pas, a.fils)
        print(f"{f} : {len(data[f])} jetons lus", file=sys.stderr)
    L = ["Momentum Flap (hypothèse H8) : entrée à T si achats cumulés >= Y ; net de frais et taxes ; impact d'entrée non compté.",
         "Retenu seulement si 'sans top3' > 1 sur CHAQUE fenêtre avec n >= 15."]
    retenus = []
    for T in T_LIST:
        for Y in Y_LIST:
            for s in SORTIES:
                cell = []
                ok = True
                for f, jetons in data.items():
                    nets = []
                    for j in jetons.values():
                        r = evaluer(j, T, Y)
                        if r is None:
                            continue
                        ta, tv = j["taxe"]
                        nets.append(min(r[s] * (1 - 0.01 - ta / 1e4) * (1 - 0.01 - tv / 1e4), 1e4))
                    nets.sort(reverse=True)
                    n = len(nets)
                    moy = st.mean(nets) if nets else 0
                    s3 = st.mean(nets[3:]) if n > 3 else 0
                    cell.append(f"{f[8:10]}/{f[5:7]} {f[11:13]}h n={n} moy x{moy:.3f} s3 x{s3:.3f}")
                    if n < 15 or s3 <= 1:
                        ok = False
                L.append(f"T={T:>3}s Y={Y:>4}$ {s:<11} | " + " | ".join(cell) + ("   <= TIENT" if ok else ""))
                if ok:
                    retenus.append((T, Y, s))
    L.append(f"Cases qui tiennent sur les 2 fenêtres : {retenus if retenus else 'aucune'}")
    print(ecrire_txt("momentum_flap.txt", L))


if __name__ == "__main__":
    main()
