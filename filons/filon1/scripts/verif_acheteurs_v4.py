"""Vérifie les premiers acheteurs d'un échantillon de pools V4 (sortie de mesure_v4.py) :
qui paie, par quel routeur, quel nonce, quel pourboire, et s'ils ont revendu (revente prouvée) dans les 120 s.

Usage :
  RPC_URL=https://rpc.mainnet.arc.io python verif_acheteurs_v4.py --pools cache/arc_semaine_pools.json \
     --pm 0x8366a39CC670B4001A1121B8F6A443A643e40951 --routeur 0x4fcA4a51Ab4F23A7447b3284fBd7D73289A89Fb1 \
     --jour 2026-10-30 --n 40 --quote 0x0000000000000000000000000000000000000000:1:18 --nom verif_arc_3010

Un « extérieur probable » : paie lui-même (from), passe par le routeur public, nonce >= 20, n'est pas le créateur.
La caisse commune (même financeur) n'est PAS vérifiée ici : il faudrait un explorateur.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
from collections import defaultdict

from commun import ecrire_txt, en_parallele, rpc
from mesure_v4 import SWAP, h2i, mot, txs

Q96 = 2**96


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", required=True)
    ap.add_argument("--pm", required=True)
    ap.add_argument("--routeur", required=True, help="routeur public (Universal Router)")
    ap.add_argument("--jour", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--quote", default="0x0000000000000000000000000000000000000000:1:18")
    ap.add_argument("--blocs", type=int, default=400, help="fenêtre suivie après la création (en blocs)")
    ap.add_argument("--nom", required=True)
    a = ap.parse_args()
    routeur = a.routeur.lower()
    qadr, qpx, qdec = a.quote.split(":")
    qpx, qdec = float(qpx), int(qdec)

    pools = [p for p in json.load(open(a.pools)) if dt.datetime.fromtimestamp(p["ts"], dt.UTC).strftime("%Y-%m-%d") == a.jour]
    pools.sort(key=lambda p: p["bloc"])
    k = max(1, len(pools) // a.n)
    echant = pools[::k][: a.n]

    def swaps(p):
        return p, rpc("eth_getLogs", [{"address": a.pm, "fromBlock": hex(p["bloc"]), "toBlock": hex(p["bloc"] + a.blocs),
                                        "topics": [SWAP, p["id"]]}])

    data = en_parallele(swaps, echant, fils=4)
    hashes = list({l["transactionHash"] for _, ls in data for l in ls})
    tx = txs(hashes, 4)

    # reçus (gaz payé) sur un sous-échantillon
    def recu(h):
        try:
            return h, rpc("eth_getTransactionReceipt", [h])
        except Exception:
            return h, None
    recus = dict(en_parallele(recu, hashes[:300], fils=4))
    gaz = [h2i(r["gasUsed"]) * h2i(r.get("effectiveGasPrice", "0x0")) / 1e18 * qpx for r in recus.values() if r]
    echecs = sum(1 for r in recus.values() if r and r.get("status") == "0x0")

    stats = defaultdict(int)
    from collections import Counter
    vers = Counter()
    pnl_ext, delais, nonces, tips = [], [], [], []
    for p, ls in data:
        ls.sort(key=lambda l: (h2i(l["blockNumber"]), h2i(l["logIndex"])))
        createur = (p.get("createur") or "").lower()
        par_payeur = defaultdict(lambda: {"in": 0.0, "out": 0.0, "t_in": None, "t_out": None})
        for l in ls:
            b = h2i(l["blockNumber"])
            t = tx.get(l["transactionHash"], {})
            frm, to, nonce = t.get("from"), t.get("to"), t.get("nonce", 0)
            a0 = mot(l["data"], 0, True)
            u = -a0 / 10**qdec * qpx  # > 0 : achat (cotation = currency0)
            if abs(u) < 5:
                continue
            ext = frm and frm != createur and to == routeur and nonce >= 20
            if b <= p["bloc"] + 3 and u > 0:
                vers[to] += 1
                stats["achats_blocs_1_3"] += 1
                stats["achats_blocs_1_3_ext"] += int(bool(ext))
                if u >= 100:
                    stats["achats_blocs_1_3_100usd"] += 1
                nonces.append(nonce)
            if not frm:
                continue
            d = par_payeur[frm]
            if u > 0:
                d["in"] += u
                d["t_in"] = d["t_in"] or b
            else:
                d["out"] += -u
                d["t_out"] = b
            d["ext"] = ext
        for frm, d in par_payeur.items():
            if d["in"] and d.get("ext") and d["t_in"] <= p["bloc"] + 3:
                stats["ext_entres_tot"] += 1
                if d["out"]:
                    stats["ext_revendu"] += 1
                    pnl_ext.append(d["out"] / d["in"])
                    delais.append((d["t_out"] - d["t_in"]) * 0.5)
    for h, t in tx.items():
        pass
    L = [f"{a.nom} : {len(echant)} pools du {a.jour} (1 sur {k}), {a.blocs} blocs suivis, {len(hashes)} tx de swap.",
         f"Achats >= 5 $ dans les blocs +1 à +3 : {stats['achats_blocs_1_3']} ; dont >= 100 $ : {stats['achats_blocs_1_3_100usd']} ; "
         f"dont extérieurs probables (payeur propre, routeur public, nonce >= 20) : {stats['achats_blocs_1_3_ext']}.",
         f"Nonce médian de ces premiers acheteurs : {st.median(nonces) if nonces else 'n/a'}.",
         f"Extérieurs entrés dans les blocs +1 à +3 : {stats['ext_entres_tot']} ; ayant revendu (vente réussie vue) : {stats['ext_revendu']}"
         + (f" ; multiple réalisé médian x{st.median(pnl_ext):.2f}, moyen x{st.mean(pnl_ext):.2f} ; délai médian {st.median(delais):.0f} s" if pnl_ext else ""),
         f"Gaz payé par swap (médiane sur {len(gaz)} reçus) : {st.median(gaz) if gaz else 0:.4f} $ ; tx en échec parmi ces reçus : {echecs}.",
         "Contrats appelés par ces premiers acheteurs (to) : " + ", ".join(f"{x} {n}" for x, n in vers.most_common(4)),
         "Limite : les ventes en échec d'autres pools/routeurs et la caisse commune ne sont pas vues ici."]
    print(ecrire_txt(f"{a.nom}.txt", L))


if __name__ == "__main__":
    main()
