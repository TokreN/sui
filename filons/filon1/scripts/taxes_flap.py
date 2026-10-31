"""Lit la taxe réelle (achat / vente) des jetons Flap mesurés et recalcule « +60 % en 120 s » net de frais.

Usage : RPC_URL=https://bsc-rpc.publicnode.com python taxes_flap.py flap_3010 flap_2910
Entrée : cache/<nom>_jetons.json (sortie de mesure_flap.py). Sortie : taxes_flap.txt.
Lecture : Portal.getTokenV8Safe(token) -> 18 mots ; buyTaxRate = mot 12, sellTaxRate = mot 13 (points de base),
d'après la doc Flap (docs.flap.sh). État lu « à l'instant » (bloc latest).
Net = s60 x (1 - 1 % - taxe achat) x (1 - 1 % - taxe vente) : frais de base 1 % par trade + taxe en plus (doc Flap).
Gaz (~0,0035 $ par tx) et impact sur la courbe ne sont pas comptés.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
import urllib.request
from collections import Counter, defaultdict

from commun import CACHE_DIR, ecrire_txt, en_parallele, keccak256

PORTAL = "0xe2cE6ab80874Fa9Fa2aAE65D277Dd6B8e65C9De0"
SEL = "0x" + keccak256(b"getTokenV8Safe(address)").hex()[:8]


def lots_taxes(jetons):
    def un(lot):
        corps = [{"jsonrpc": "2.0", "id": i, "method": "eth_call",
                  "params": [{"to": PORTAL, "data": SEL + "0" * 24 + t[2:]}, "latest"]} for i, t in enumerate(lot)]
        req = urllib.request.Request(os.environ["RPC_URL"], data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "filon1"})
        for _ in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    rep = json.loads(r.read())
                out = {}
                for x in rep if isinstance(rep, list) else []:
                    d = x.get("result")
                    if d and len(d) >= 2 + 64 * 18:
                        w = lambda k: int(d[2 + 64 * k: 2 + 64 * (k + 1)], 16)
                        out[lot[x["id"]]] = (w(12), w(13))
                return out
            except Exception:
                import time
                time.sleep(2)
        return {}
    res = {}
    for o in en_parallele(un, [jetons[i: i + 25] for i in range(0, len(jetons), 25)], fils=3):
        res.update(o)
    return res


def main():
    noms = sys.argv[1:] or ["flap_3010"]
    L = [f"Taxes Flap lues via Portal.getTokenV8Safe ({SEL}), bloc latest."]
    for nom in noms:
        rs = sorted(json.load(open(os.path.join(CACHE_DIR, f"{nom}_jetons.json"))), key=lambda r: r["ts"])
        tx = lots_taxes([r["jeton"] for r in rs])
        vu = defaultdict(int)
        for r in rs:
            r["nouveau"] = vu[r["createur"]] == 0
            vu[r["createur"]] += 1
            bt, stx = tx.get(r["jeton"], (None, None))
            r["taxe_achat"], r["taxe_vente"] = bt, stx
            if bt is not None:
                r["net"] = r["s60"] * (1 - 0.01 - bt / 1e4) * (1 - 0.01 - stx / 1e4)
        lus = [r for r in rs if r.get("net") is not None]
        dist = Counter((r["taxe_achat"], r["taxe_vente"]) for r in lus)
        L.append(f"{nom} : taxes lues pour {len(lus)} sur {len(rs)} jetons ; (achat, vente) en points de base les plus fréquents : "
                 + ", ".join(f"{k} {n}" for k, n in dist.most_common(5)))
        for seg, f in (("tous", lambda r: True), ("nouveau créateur", lambda r: r["nouveau"]), ("créateur déjà vu", lambda r: not r["nouveau"])):
            s = [r for r in lus if f(r)]
            if not s:
                continue
            nets = sorted((r["net"] for r in s), reverse=True)
            L.append(f"  {seg} : n {len(s)} ; +60 %/120 s brut x{st.mean(r['s60'] for r in s):.3f} ; net de frais et taxes x{st.mean(nets):.3f} ; "
                     f"net sans top 3 x{st.mean(nets[3:]) if len(nets) > 3 else 0:.3f}")
        with open(os.path.join(CACHE_DIR, f"{nom}_jetons_taxes.json"), "w", encoding="utf-8") as fch:
            json.dump(rs, fch)
    print(ecrire_txt("taxes_flap.txt", L))


if __name__ == "__main__":
    main()
