"""Filtre anti-piège à lancer AVANT un achat. Lit seulement des données publiques (RPC_URL, aucune clé).
Répond NO-GO avec les raisons, ou « aucun piège détecté ». Signatures tirées des mesures du filon 1 (JOURNAL.md).

Exemples :
  RPC_URL=https://rpc.mainnet.arc.io python filtre_pieges.py v4 --pm 0x8366a39CC670B4001A1121B8F6A443A643e40951 \
      --routeur 0x4fcA4a51Ab4F23A7447b3284fBd7D73289A89Fb1 --pool 0x<id du pool> --mise 105
  RPC_URL=https://hyperliquid-json-rpc.stakely.io python filtre_pieges.py v2 --pair 0x<pair> --quote 0x5555555555555555555555555555555555555555:88:18 --pas 1000 --mise 105
  RPC_URL=https://bsc-rpc.publicnode.com python filtre_pieges.py flap --token 0x<jeton> --prix-natif 706 --mise 105

Signaux de NO-GO (un seul suffit) :
  - LP retirée (>= 50 % de la liquidité ajoutée) : rug (Arc : 76 % des pools en ~4,5 min).
  - Premiers achats concentrés sur <= 2 contrats privés (pas le routeur public) : flotte (Arc : 100 %).
  - Nonce médian des premiers payeurs >= 5 000 (robots) ou <= 2 (wallets neufs, HyperEVM : 1).
  - Le contrat qui achète est aussi celui qui retire la LP.
  - Coût de départ (frais + taxes + ton impact, aller-retour) > 8 % : il faut trop de hausse pour revenir à zéro.
  - Flap : créateur en série (>= 3 jetons dans l'heure) ; ses jetons font x0,86 net en moyenne.
« Aucun piège détecté » ne veut PAS dire rentable : sur les lieux mesurés, l'espérance reste négative même sans piège.
Sortie : affichage + une ligne ajoutée à filtre_pieges.txt.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import statistics as st
import sys

from commun import ICI, rpc, sujet
from mesure_v4 import INIT, MODLIQ, SWAP as SWAP4, h2i, mot, txs

Q96 = 2**96
SWAP2 = sujet("Swap(address,uint256,uint256,uint256,uint256,address)")
SYNC2 = sujet("Sync(uint112,uint112)")
BURN2 = sujet("Burn(address,uint256,uint256,address)")
MINT2 = sujet("Mint(address,uint256,uint256)")


def logs_plage(filtre, de, a, pas):
    out = []
    x = de
    while x <= a:
        y = min(x + pas - 1, a)
        try:
            out += rpc("eth_getLogs", [{**filtre, "fromBlock": hex(x), "toBlock": hex(y)}], essais=4)
        except Exception:
            if y - x < 20:
                raise
            m = (x + y) // 2
            out += logs_plage(filtre, x, m, max(10, (m - x + 1)))
            out += logs_plage(filtre, m + 1, y, max(10, (y - m)))
        x = y + 1
    return out


def signaux_acheteurs(hashes, routeur, createur):
    """Concentration des contrats, nonce des payeurs, parmi les premiers achats."""
    t = txs(hashes, 3)
    lignes = [t[h] for h in hashes if h in t]
    if not lignes:
        return [], {}, None
    vers = {}
    for x in lignes:
        vers[x["to"]] = vers.get(x["to"], 0) + 1
    nonces = [x["nonce"] for x in lignes]
    med = st.median(nonces)
    raisons = []
    prives = {k: v for k, v in vers.items() if k and k != routeur}
    part_privee = sum(prives.values()) / len(lignes)
    if len(lignes) >= 5 and part_privee >= 0.8 and len(prives) <= 2:
        raisons.append(f"flotte : {part_privee:.0%} des {len(lignes)} premiers achats passent par {len(prives)} contrat(s) privé(s)")
    if len(lignes) >= 5 and med >= 5000:
        raisons.append(f"acheteurs = robots (nonce médian {med:.0f})")
    if len(lignes) >= 5 and med <= 2:
        raisons.append(f"acheteurs = wallets neufs (nonce médian {med:.0f})")
    if createur and sum(1 for x in lignes if x["from"] == createur) >= 2:
        raisons.append("le créateur achète lui-même au début")
    return raisons, vers, med


def verif_v4(a):
    tete = h2i(rpc("eth_blockNumber", []))
    pool = a.pool.lower()
    ini = logs_plage({"address": a.pm, "topics": [INIT, pool]}, max(1, tete - a.recul), tete, a.pas)
    if not ini:
        return "INCONNU", [f"pool introuvable dans les {a.recul} derniers blocs (augmente --recul)"]
    l = ini[0]
    c0, c1 = "0x" + l["topics"][2][-40:], "0x" + l["topics"][3][-40:]
    quotes = {q.split(":")[0].lower(): (float(q.split(":")[1]), int(q.split(":")[2])) for q in a.quote.split(",")}
    if c0 in quotes:
        cote, (px, dec) = 0, quotes[c0]
    elif c1 in quotes:
        cote, (px, dec) = 1, quotes[c1]
    else:
        return "INCONNU", ["devise de cotation inconnue (ajoute-la dans --quote)"]
    b_c = h2i(l["blockNumber"])
    hooks = "0x" + l["data"][2 + 64 * 2 + 24: 2 + 64 * 3]
    tc = txs([l["transactionHash"]], 1).get(l["transactionHash"], {})
    createur = tc.get("from")
    raisons = []
    # LP
    liq = logs_plage({"address": a.pm, "topics": [MODLIQ, pool]}, b_c, tete, a.pas)
    aj = re = 0
    t_rug_bloc = None
    rug_tx = None
    for x in sorted(liq, key=lambda x: (h2i(x["blockNumber"]), h2i(x["logIndex"]))):
        d = mot(x["data"], 2, True)
        if d > 0:
            aj += d
        else:
            re += -d
        if aj and re >= 0.5 * aj and t_rug_bloc is None:
            t_rug_bloc, rug_tx = h2i(x["blockNumber"]), x["transactionHash"]
    if t_rug_bloc is not None:
        raisons.append(f"LP retirée (rug) {t_rug_bloc - b_c} blocs après la création")
    # premiers achats
    sw = logs_plage({"address": a.pm, "topics": [SWAP4, pool]}, b_c, min(tete, b_c + a.fenetre), a.pas)
    sw.sort(key=lambda x: (h2i(x["blockNumber"]), h2i(x["logIndex"])))
    achats = []
    dernier = None
    for x in sw:
        q = mot(x["data"], 0 if cote == 0 else 1, True)
        u = -q / 10**dec * px
        dernier = x
        if u >= 5:
            achats.append(x["transactionHash"])
    r, vers, med = signaux_acheteurs(achats[:20], a.routeur.lower(), createur)
    raisons += r
    if rug_tx:
        to_rug = txs([rug_tx], 1).get(rug_tx, {}).get("to")
        if to_rug and to_rug in vers and to_rug != a.routeur.lower():
            raisons.append(f"le contrat qui achète ({to_rug[:10]}…) est celui qui retire la LP")
    # impact de ta mise (une seule plage de liquidité, approximation)
    imp = None
    src = dernier or l
    if dernier:
        sp, L = mot(dernier["data"], 2) / Q96, mot(dernier["data"], 3)
    else:
        sp, L = mot(l["data"], 3) / Q96, 0
    if L and sp:
        A = a.mise * 1.08 / px * 10**dec
        if cote == 0:
            spn = 1 / (1 / sp + A / L)
            out = L * (sp - spn)
            imp = (A / out) / (1 / sp**2) - 1 if out > 0 else None
        else:
            spn = sp + A / L
            out = L * (1 / sp - 1 / spn)
            imp = (A / out) / (sp**2) - 1 if out > 0 else None
    frais = mot(l["data"], 0) / 1e6 if mot(l["data"], 0) < 1_000_000 else 0.01
    if imp is not None:
        cout = 1 - (1 - frais - imp) ** 2
        if cout > 0.08:
            raisons.append(f"coût de départ {cout:.1%} (frais {frais:.2%} + impact {imp:.1%}, aller-retour) : trop lourd")
    if int(hooks, 16):
        raisons.append(f"hook présent ({hooks[:10]}…) : vérifie qu'on peut revendre (simulation) avant d'acheter")
    nogo = [x for x in raisons if not x.startswith("hook")]
    return ("NO-GO" if nogo else "aucun piège détecté"), raisons


def verif_v2(a):
    tete = h2i(rpc("eth_blockNumber", []))
    pair = a.pair.lower()
    quotes = {q.split(":")[0].lower(): (float(q.split(":")[1]), int(q.split(":")[2])) for q in a.quote.split(",")}
    t0 = "0x" + rpc("eth_call", [{"to": pair, "data": "0x0dfe1681"}, "latest"])[-40:]
    t1 = "0x" + rpc("eth_call", [{"to": pair, "data": "0xd21220a7"}, "latest"])[-40:]
    if t0 in quotes:
        cote, (px, dec) = 0, quotes[t0]
    elif t1 in quotes:
        cote, (px, dec) = 1, quotes[t1]
    else:
        return "INCONNU", ["devise de cotation inconnue (ajoute-la dans --quote)"]
    ev = logs_plage({"address": pair, "topics": [[MINT2, SYNC2, SWAP2, BURN2]]}, max(1, tete - a.recul), tete, a.pas)
    ev.sort(key=lambda x: (h2i(x["blockNumber"]), h2i(x["logIndex"])))
    mints = [x for x in ev if x["topics"][0] == MINT2]
    if not mints:
        return "INCONNU", [f"pas de liquidité ajoutée dans les {a.recul} derniers blocs (augmente --recul)"]
    b_c = h2i(mints[0]["blockNumber"])
    tc = txs([mints[0]["transactionHash"]], 1).get(mints[0]["transactionHash"], {})
    createur = tc.get("from")
    raisons = []
    rq = rq_max = 0
    achats = []
    vu_achat = vu_vente = 0
    for x in ev:
        top, d = x["topics"][0], x["data"]
        if top == SYNC2:
            r0, r1 = mot(d, 0), mot(d, 1)
            rq = r0 if cote == 0 else r1
            rq_max = max(rq_max, rq)
        elif top == BURN2:
            q_out = mot(d, 0) if cote == 0 else mot(d, 1)
            if rq_max and q_out >= 0.5 * (rq + q_out):
                raisons.append(f"LP retirée (rug) {h2i(x['blockNumber']) - b_c} blocs après la liquidité")
        elif top == SWAP2:
            qin = mot(d, 0) if cote == 0 else mot(d, 1)
            qout = mot(d, 2) if cote == 0 else mot(d, 3)
            if qin / 10**dec * px >= 5:
                vu_achat += 1
                if h2i(x["blockNumber"]) <= b_c + a.fenetre:
                    achats.append(x["transactionHash"])
            if qout / 10**dec * px >= 5:
                vu_vente += 1
    if vu_achat >= 5 and vu_vente == 0:
        raisons.append(f"{vu_achat} achats et 0 vente : revente peut-être bloquée")
    r, vers, med = signaux_acheteurs(achats[:20], (a.routeur or "").lower(), createur)
    raisons += r
    if rq:
        reserve_usd = rq / 10**dec * px
        imp = (a.mise * 1.08) / reserve_usd if reserve_usd else 1
        cout = 1 - (1 - 0.003 - imp) ** 2
        if cout > 0.08:
            raisons.append(f"coût de départ {cout:.1%} (réserve {reserve_usd:,.0f} $, impact ~{imp:.1%}) : trop lourd")
    return ("NO-GO" if raisons else "aucun piège détecté"), raisons


def verif_flap(a):
    from exits_flap import ACHAT, CREE, PORTAL, SELV8
    tete = h2i(rpc("eth_blockNumber", []))
    tok = a.token.lower()
    d = rpc("eth_call", [{"to": PORTAL, "data": SELV8 + "0" * 24 + tok[2:]}, "latest"])
    if not d or len(d) < 2 + 64 * 18:
        return "INCONNU", ["jeton inconnu du Portal Flap"]
    w = lambda i: int(d[2 + 64 * i: 2 + 64 * (i + 1)], 16)
    bt, stx = w(12), w(13)
    raisons = []
    # taxe + impact (impact médian mesuré sur Flap : 3,2 % à ~105 €, 10,8 % à ~420 €)
    imp = 0.032 if a.mise <= 150 else (0.108 if a.mise >= 350 else 0.032 + (a.mise - 150) / 200 * 0.076)
    cout = 1 - (1 - 0.01 - bt / 1e4 - imp) * (1 - 0.01 - stx / 1e4 - imp)
    if cout > 0.08:
        raisons.append(f"coût de départ {cout:.0%} (taxe {bt / 100:.0f} % / {stx / 100:.0f} %, frais 1 %, impact ~{imp:.0%}) : "
                       f"il faut +{1 / (1 - cout) - 1:.0%} juste pour revenir à zéro")
    # créateur et son rythme
    cre = []
    x = max(1, tete - a.recul)
    while x <= tete:
        y = min(x + a.pas - 1, tete)
        cre += rpc("eth_getLogs", [{"address": PORTAL, "topics": [CREE], "fromBlock": hex(x), "toBlock": hex(y)}])
        x = y + 1
    createur = None
    b_c = None
    for l in cre:
        dd = l["data"]
        if "0x" + dd[2 + 64 * 3 + 24: 2 + 64 * 4] == tok:
            createur = "0x" + dd[2 + 64 + 24: 2 + 128]
            b_c = h2i(l["blockNumber"])
    if createur:
        n = sum(1 for l in cre if "0x" + l["data"][2 + 64 + 24: 2 + 128] == createur
                and abs(h2i(l["blockNumber"]) - b_c) <= 8000)
        if n >= 3:
            raisons.append(f"créateur en série : {n} jetons dans l'heure autour de celui-ci")
        # premiers achats de ce jeton
        tr = rpc("eth_getLogs", [{"address": PORTAL, "topics": [ACHAT], "fromBlock": hex(b_c), "toBlock": hex(min(tete, b_c + a.fenetre))}])
        hs = [l["transactionHash"] for l in tr if "0x" + l["data"][2 + 64 + 24: 2 + 128] == tok][:20]
        r, vers, med = signaux_acheteurs(hs, PORTAL.lower(), createur)
        raisons += [x for x in r if not x.startswith("flotte")]  # sur Flap, les achats passent par des contrats publics
    else:
        raisons.append(f"création non trouvée dans les {a.recul} derniers blocs : créateur et premiers acheteurs non vérifiés")
    nogo = [x for x in raisons if not x.startswith("création non trouvée")]
    return ("NO-GO" if nogo else "aucun piège détecté"), raisons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("type", choices=["v4", "v2", "flap"])
    ap.add_argument("--pm")
    ap.add_argument("--pool")
    ap.add_argument("--pair")
    ap.add_argument("--token")
    ap.add_argument("--routeur", default="")
    ap.add_argument("--quote", default="0x0000000000000000000000000000000000000000:1:18,0x3600000000000000000000000000000000000000:1:6")
    ap.add_argument("--prix-natif", type=float, default=706)
    ap.add_argument("--mise", type=float, default=105, help="mise en euros")
    ap.add_argument("--recul", type=int, default=40000, help="blocs à remonter pour retrouver la création")
    ap.add_argument("--fenetre", type=int, default=2000, help="blocs après la création pour lire les premiers achats")
    ap.add_argument("--pas", type=int, default=9999)
    a = ap.parse_args()
    if a.type == "v4":
        verdict, raisons = verif_v4(a)
        cible = a.pool
    elif a.type == "v2":
        verdict, raisons = verif_v2(a)
        cible = a.pair
    else:
        verdict, raisons = verif_flap(a)
        cible = a.token
    print(f"{verdict} — {a.type} {cible} (mise {a.mise:.0f} €)")
    for r in raisons:
        print("  -", r)
    if verdict == "aucun piège détecté":
        print("  (rappel : aucun piège ne veut pas dire rentable ; l'espérance mesurée reste négative sur les lieux du filon 1)")
    with open(os.path.join(ICI, "filtre_pieges.txt"), "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now(dt.UTC):%Y-%m-%d %H:%M} | {verdict} | {a.type} {cible} | " + " ; ".join(raisons) + "\n")


if __name__ == "__main__":
    main()
