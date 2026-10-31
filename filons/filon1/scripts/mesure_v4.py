"""Mesure d'un lieu Uniswap V4 (toute chaîne EVM) à partir des événements du PoolManager.

Compte TOUS les pools créés (événements Initialize), pas seulement les survivants.
RPC : variable d'environnement RPC_URL. Aucune clé dans le code.

Exemple (Arc, pools nés le 30/10/2026, suivi 24 h) :
  RPC_URL=https://rpc.mainnet.arc.io python mesure_v4.py --pm 0x8366a39CC670B4001A1121B8F6A443A643e40951 \
      --debut 2026-10-30T00:00 --fin 2026-10-31T00:00 --suivi 24 --nom arc_3010

Sorties : <nom>.txt (court) et cache/<nom>_pools.json (une ligne par pool).

Définitions (écrites avant de compter, voir JOURNAL.md) :
- entrée = prix à la fin du bloc de création + 2 (jamais le bloc 0) ;
- swaps < 5 $ ignorés pour les plus hauts (poussière) ;
- actif = >= 220 $ achetés dans les 24 h ; x5 = plus haut 24 h >= 5x l'entrée, avec >= 2 200 $ achetés en 24 h ;
  au-delà de x10 000 : artefact, ignoré ;
- x10 / x100 = plus haut 7 j / entrée ; tenir 7 j = prix à J+7 / entrée ;
- « +60 % en 120 s » = vendre dès +60 % si atteint dans les 120 s après l'entrée, sinon vendre au prix à 120 s ;
- morte à 7 j = aucun swap >= 5 $ entre J+6 et J+7, ou prix à J+7 < 10 % de l'entrée ;
- créateur = expéditeur (from) de la transaction qui crée le pool ; usine = destinataire (to) de cette transaction.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
import sys
from collections import Counter, defaultdict

from commun import CACHE_DIR, ecrire_txt, en_parallele, rpc

INIT = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
MODLIQ = "0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec"
Q96 = 2**96


def h2i(x: str) -> int:
    return int(x, 16)


def mot(data: str, i: int, signe: bool = False) -> int:
    b = bytes.fromhex(data[2 + 64 * i: 2 + 64 * (i + 1)])
    return int.from_bytes(b, "big", signed=signe)


def ts_bloc(b: int) -> int:
    return h2i(rpc("eth_getBlockByNumber", [hex(b), False], cache=True)["timestamp"])


def bloc_a(ts: int, tete: int) -> int:
    """Premier bloc dont l'horodatage est >= ts (recherche dichotomique)."""
    lo, hi = 1, tete
    while lo < hi:
        m = (lo + hi) // 2
        if ts_bloc(m) < ts:
            lo = m + 1
        else:
            hi = m
    return lo


def logs(pm: str, topics: list, de: int, a: int, pas: int, fils: int):
    tranches = [(x, min(x + pas - 1, a)) for x in range(de, a + 1, pas)]

    def un(t):
        return rpc("eth_getLogs", [{"address": pm, "fromBlock": hex(t[0]), "toBlock": hex(t[1]), "topics": topics}])

    out = []
    for r in en_parallele(un, tranches, fils=fils):
        out.extend(r)
    return out


def txs(hashes: list[str], fils: int):
    """Transactions par lots (from, to, nonce). Relance les manquantes ; cache disque."""
    import time
    import urllib.request

    chemin = os.path.join(CACHE_DIR, "txs.json")
    try:
        with open(chemin, encoding="utf-8") as f:
            res = json.load(f)
    except Exception:
        res = {}

    def un(lot):
        corps = [{"jsonrpc": "2.0", "id": i, "method": "eth_getTransactionByHash", "params": [h]} for i, h in enumerate(lot)]
        req = urllib.request.Request(os.environ["RPC_URL"], data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "filon1"})
        for essai in range(4):
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    rep = json.loads(r.read())
                return rep if isinstance(rep, list) else []
            except Exception:
                time.sleep(2 * (essai + 1))
        return []

    for tour in range(5):
        manque = [h for h in dict.fromkeys(hashes) if h not in res]
        if not manque:
            break
        lots = [manque[i: i + 20] for i in range(0, len(manque), 20)]
        for rep in en_parallele(un, lots, fils=max(2, fils // (tour + 1))):
            for x in rep:
                t = x.get("result") if isinstance(x, dict) else None
                if t:
                    res[t["hash"]] = {"from": t["from"].lower(), "to": (t.get("to") or "").lower(), "nonce": h2i(t["nonce"])}
        time.sleep(1 + tour)
    manque = [h for h in hashes if h not in res]
    if manque:
        print(f"  transactions introuvables : {len(manque)} sur {len(hashes)}", file=sys.stderr)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(res, f)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pm", required=True, help="adresse du PoolManager V4")
    ap.add_argument("--debut", required=True, help="naissance des pools, début (UTC, AAAA-MM-JJTHH:MM)")
    ap.add_argument("--fin", required=True, help="naissance des pools, fin (UTC)")
    ap.add_argument("--suivi", type=float, default=24, help="heures de suivi après la fin (24 ou 168)")
    ap.add_argument("--quote", default="0x0000000000000000000000000000000000000000:1:18",
                    help="devises de cotation adresse:prix_usd:decimales, séparées par des virgules")
    ap.add_argument("--pas", type=int, default=9999, help="taille max d'une plage eth_getLogs")
    ap.add_argument("--fils", type=int, default=8)
    ap.add_argument("--nom", required=True)
    ap.add_argument("--ids-par-appel", type=int, default=150)
    ap.add_argument("--echantillon", type=int, default=0, help="nombre max de pools mesurés (échantillon uniforme)")
    a = ap.parse_args()

    quotes = {}
    for q in a.quote.split(","):
        ad, px, dec = q.split(":")
        quotes[ad.lower()] = (float(px), int(dec))

    t0 = int(dt.datetime.fromisoformat(a.debut).replace(tzinfo=dt.UTC).timestamp())
    t1 = int(dt.datetime.fromisoformat(a.fin).replace(tzinfo=dt.UTC).timestamp())
    t2 = t1 + int(a.suivi * 3600)
    tete = h2i(rpc("eth_blockNumber", []))
    b0, b1 = bloc_a(t0, tete), bloc_a(t1, tete)
    b2 = min(bloc_a(t2, tete), tete) if t2 < ts_bloc(tete) else tete
    print(f"blocs {b0} -> {b1} (naissances), suivi jusqu'à {b2}", file=sys.stderr)

    # 1) toutes les créations de pools
    ini = logs(a.pm, [INIT], b0, b1 - 1, a.pas, a.fils)
    pools = {}
    hors_usd = 0
    for l in ini:
        pid = l["topics"][1]
        c0 = "0x" + l["topics"][2][-40:]
        c1 = "0x" + l["topics"][3][-40:]
        if c0 in quotes:
            cote = 0
        elif c1 in quotes:
            cote = 1
        else:
            hors_usd += 1
            continue
        pools[pid] = {
            "id": pid, "bloc": h2i(l["blockNumber"]), "tx": l["transactionHash"],
            "ts": h2i(l["blockTimestamp"]) if l.get("blockTimestamp") else None,
            "c0": c0, "c1": c1, "cote": cote, "fee": mot(l["data"], 0), "hooks": "0x" + l["data"][2 + 64 * 2 + 24: 2 + 64 * 3],
            "sqrt0": mot(l["data"], 3), "swaps": [], "liq": [],
        }
    print(f"pools créés : {len(ini)} (cotés USD : {len(pools)}, autres : {hors_usd})", file=sys.stderr)
    # créations par jour (tous les pools, avant échantillonnage)
    par_jour = Counter()
    for l in ini:
        tsl = h2i(l["blockTimestamp"]) if l.get("blockTimestamp") else None
        if tsl:
            par_jour[dt.datetime.fromtimestamp(tsl, dt.UTC).strftime("%Y-%m-%d")] += 1
    a.par_jour = dict(sorted(par_jour.items()))
    a.n_usd_total = len(pools)
    a.pas_echantillon = 1
    if a.echantillon and len(pools) > a.echantillon:
        # échantillon uniforme dans l'ordre des blocs (1 pool sur k), sans regarder la suite : pas d'information du futur
        k = -(-len(pools) // a.echantillon)
        garde = sorted(pools.values(), key=lambda p: (p["bloc"], p["id"]))[::k]
        pools = {p["id"]: p for p in garde}
        a.pas_echantillon = k
        print(f"échantillon : 1 pool sur {k} -> {len(pools)}", file=sys.stderr)

    # 2) swaps et liquidité de ces pools (filtre par id, OR de topics)
    ids = list(pools)
    for i in range(0, len(ids), a.ids_par_appel):
        lot = ids[i: i + a.ids_par_appel]
        for l in logs(a.pm, [SWAP, lot], b0, b2, a.pas, a.fils):
            p = pools[l["topics"][1]]
            p["swaps"].append((h2i(l["blockNumber"]), h2i(l["logIndex"]),
                               h2i(l["blockTimestamp"]) if l.get("blockTimestamp") else None,
                               mot(l["data"], 0, True), mot(l["data"], 1, True), mot(l["data"], 2), mot(l["data"], 3),
                               mot(l["data"], 5), l["transactionHash"]))
        for l in logs(a.pm, [MODLIQ, lot], b0, b2, a.pas, a.fils):
            p = pools[l["topics"][1]]
            p["liq"].append((h2i(l["blockNumber"]), mot(l["data"], 2, True),
                             h2i(l["blockTimestamp"]) if l.get("blockTimestamp") else None))
        print(f"  swaps lus pour {min(i + a.ids_par_appel, len(ids))}/{len(ids)} pools", file=sys.stderr)

    # 3) créateurs et usines
    tx = txs([p["tx"] for p in pools.values()], a.fils)
    for p in pools.values():
        t = tx.get(p["tx"], {})
        p["createur"], p["usine"] = t.get("from"), t.get("to")

    # horodatage : bloc -> ts (interpolation si le RPC ne donne pas blockTimestamp)
    tsb0, tsb2 = ts_bloc(b0), ts_bloc(b2)
    def ts_de(b, ts):
        return ts if ts else tsb0 + (b - b0) * (tsb2 - tsb0) / max(b2 - b0, 1)

    # 4) mesures par pool
    res = []
    for p in pools.values():
        p["swaps"].sort()
        px_usd, dec = quotes[p["c0"] if p["cote"] == 0 else p["c1"]]

        def prix(s):  # prix du jeton en unités de cotation (brut, sans décimales : seuls les rapports servent)
            r = (s / Q96) ** 2
            return (1 / r if r else 0) if p["cote"] == 0 else r

        def usd(sw):  # montant côté cotation, en $ (positif = achat du jeton)
            q = sw[3] if p["cote"] == 0 else sw[4]
            return -q / 10**dec * px_usd  # delta négatif côté cotation = l'utilisateur paie = achat

        ent_bloc = p["bloc"] + 2
        e = prix(p["sqrt0"])
        liq_ent = None
        for sw in p["swaps"]:
            if sw[0] <= ent_bloc:
                e = prix(sw[5])
                liq_ent = sw[6]
        ts_c = ts_de(p["bloc"], p["ts"])
        apres = [sw for sw in p["swaps"] if sw[0] > ent_bloc]
        if not e:
            continue
        # retrait de LP : premier instant où le retiré cumulé >= 50 % de l'ajouté cumulé
        ajoute = retire = 0
        t_rug = None
        for b, d, tl in sorted(p["liq"], key=lambda x: x[0]):
            if d > 0:
                ajoute += d
            else:
                retire += -d
            if ajoute and retire >= 0.5 * ajoute and t_rug is None:
                t_rug = ts_de(b, tl) - ts_c
        m24 = m7 = m120 = e
        p120 = e
        dernier = e
        achats24 = ventes24 = 0.0
        n_ach = n_ven = 0
        actif_j7 = False
        t_160 = None
        for sw in apres:
            t = ts_de(sw[0], sw[2]) - ts_c
            u = usd(sw)
            x = prix(sw[5])
            if t <= 120 and abs(u) >= 5:
                m120 = max(m120, x)
                if x >= 1.6 * e and t_160 is None:
                    t_160 = t
            if t <= 120:
                p120 = x
            if t <= 7 * 86400:
                dernier = x
            if abs(u) < 5:
                continue
            if t <= 86400:
                m24 = max(m24, x)
                if u > 0:
                    achats24 += u
                    n_ach += 1
                else:
                    ventes24 += -u
                    n_ven += 1
            if t <= 7 * 86400:
                m7 = max(m7, x)
            if 6 * 86400 < t <= 7 * 86400:
                actif_j7 = True
        r24, r7 = m24 / e, m7 / e
        couvre7 = (b2 - p["bloc"]) * (tsb2 - tsb0) / max(b2 - b0, 1) >= 7 * 86400
        # stratégies : un retrait de LP avant la sortie vaut -100 %
        if t_160 is not None and (t_rug is None or t_160 < t_rug):
            s60 = 1.6
        elif t_rug is not None and t_rug <= 120:
            s60 = 0.0
        else:
            s60 = p120 / e
        tenir = None
        if couvre7:
            tenir = 0.0 if (t_rug is not None and t_rug <= 7 * 86400) else dernier / e
        # impact (approximation à une seule plage de liquidité, L au moment de l'entrée)
        imp = {}
        for taille in (110, 450):
            if liq_ent:
                sp = None
                for sw in p["swaps"]:
                    if sw[0] <= ent_bloc:
                        sp = sw[5] / Q96
                sp = sp or p["sqrt0"] / Q96
                A = taille / px_usd * 10**dec
                if p["cote"] == 0:
                    sp_new = 1 / (1 / sp + A / liq_ent)
                    out = liq_ent * (sp - sp_new)
                    exe = A / out if out > 0 else None
                    spot = 1 / sp**2
                else:
                    sp_new = sp + A / liq_ent
                    out = liq_ent * (1 / sp - 1 / sp_new)
                    exe = A / out if out > 0 else None
                    spot = sp**2
                imp[taille] = (exe / spot - 1) if exe else None
        res.append({
            "id": p["id"], "bloc": p["bloc"], "ts": int(ts_c), "createur": p["createur"], "usine": p["usine"],
            "hooks": p["hooks"], "fee": p["fee"], "n_swaps": len(p["swaps"]),
            "achats24": round(achats24, 2), "ventes24": round(ventes24, 2), "n_ach24": n_ach, "n_ven24": n_ven,
            "x24": r24, "x7": r7 if couvre7 else None, "tenir7": tenir, "s60": s60, "t_rug": t_rug,
            "x120": m120 / e, "p120": p120 / e,
            "mort7": (not actif_j7 or dernier / e < 0.1 or (t_rug is not None and t_rug <= 7 * 86400)) if couvre7 else None,
            "jeton": p["c1"] if p["cote"] == 0 else p["c0"], "imp110": imp.get(110), "imp450": imp.get(450),
            "bots_bloc_0_2": len({sw[8] for sw in p["swaps"] if sw[0] <= ent_bloc}),
        })

    with open(os.path.join(CACHE_DIR, f"{a.nom}_pools.json"), "w", encoding="utf-8") as f:
        json.dump(res, f)
    lignes = resume(res, a, len(ini), hors_usd)
    print(ecrire_txt(f"{a.nom}.txt", lignes))


def resume(res, a, n_ini, hors_usd):
    L = [f"{a.nom} : PoolManager {a.pm}, naissances {a.debut} -> {a.fin} UTC, suivi {a.suivi} h.",
         f"Pools créés : {n_ini} ; cotés USD : {a.n_usd_total} ; mesurés : {len(res)}"
         + (f" (échantillon uniforme, 1 sur {a.pas_echantillon} : compter x{a.pas_echantillon} pour les totaux)" if a.pas_echantillon > 1 else "")
         + f" ; autres cotations ignorées : {hors_usd}.",
         "Créations par jour (tous pools) : " + ", ".join(f"{j[5:]} {n}" for j, n in a.par_jour.items())]
    if not res:
        return L + ["Aucun pool mesurable."]
    jour = defaultdict(list)
    for r in res:
        jour[dt.datetime.fromtimestamp(r["ts"], dt.UTC).strftime("%Y-%m-%d")].append(r)
    L.append("jour | pools | actifs (>=220 $ achetés 24 h) | créateurs des actifs | x5 24 h (>=2 200 $ achetés) | volume achats 24 h | LP retirée < 24 h")
    for j in sorted(jour):
        rs = jour[j]
        act = [r for r in rs if r["achats24"] >= 220]
        x5 = [r for r in rs if 5 <= r["x24"] <= 10000 and r["achats24"] >= 2200]
        rg = sum(1 for r in rs if r["t_rug"] is not None and r["t_rug"] < 86400)
        L.append(f"{j} | {len(rs)} | {len(act)} | {len({r['createur'] for r in act})} | {len(x5)} | {sum(r['achats24'] for r in rs):,.0f} $ | {rg}")
    cre = Counter(r["createur"] for r in res)
    usi = Counter(r["usine"] for r in res)
    serie = {c for c, n in cre.items() if n >= 3}
    L.append(f"Créateurs : {len(cre)} ; en série (>= 3 pools) : {len(serie)} ({sum(cre[c] for c in serie)} pools).")
    L.append("Usines (to de la tx de création) : " + ", ".join(f"{u} {n}" for u, n in usi.most_common(5)))
    L.append("Familles de jetons (4 derniers caractères de l'adresse) : "
             + ", ".join(f"{s} {n}" for s, n in Counter(r["jeton"][-4:] for r in res).most_common(5)))
    rug = [r["t_rug"] for r in res if r["t_rug"] is not None]
    if rug:
        L.append(f"Retrait de LP (>= 50 %) : {len(rug)} sur {len(res)} pools ; en < 10 min : {sum(1 for t in rug if t < 600)} ; "
                 f"< 1 h : {sum(1 for t in rug if t < 3600)} ; < 24 h : {sum(1 for t in rug if t < 86400)} ; délai médian {st.median(rug) / 60:.1f} min")
    else:
        L.append(f"Retrait de LP (>= 50 %) : 0 sur {len(res)} pools")
    s60 = [r["s60"] for r in res]
    L.append(f"Stratégie +60 % en 120 s (retrait de LP = -100 %), multiple moyen avant frais : x{st.mean(s60):.3f} "
             f"(sans les 3 meilleurs : x{st.mean(sorted(s60, reverse=True)[3:]) if len(s60) > 3 else 0:.3f})")
    # grille 7 j si dispo
    r7 = [r for r in res if r["x7"] is not None]
    if r7:
        def part(rs, k):
            return f"{sum(1 for r in rs if r['x7'] >= k)} sur {len(rs)} ({100 * sum(1 for r in rs if r['x7'] >= k) / len(rs):.1f} %)"
        L.append(f"Grille 7 j sur {len(r7)} pools (tous les pools cotés USD, pas seulement les actifs) :")
        L.append(f"  x10 : {part(r7, 10)} ; x100 : {part(r7, 100)}")
        t7 = [min(r["tenir7"], 10000) for r in r7]
        L.append(f"  tenir 7 j (retrait de LP = -100 %), multiple moyen : x{st.mean(t7):.2f} ; +60 % en 120 s : x{st.mean([r['s60'] for r in r7]):.2f}")
        top = sorted(t7, reverse=True)[3:]
        L.append(f"  tenir 7 j sans les 3 meilleurs : x{st.mean(top) if top else 0:.2f}")
        L.append(f"  mortes à 7 j : {sum(1 for r in r7 if r['mort7'])} sur {len(r7)}")
        moitie = sorted(r7, key=lambda r: r["ts"])
        m1, m2 = moitie[: len(moitie) // 2], moitie[len(moitie) // 2:]
        L.append(f"  par moitié de période, tenir 7 j : x{st.mean([min(r['tenir7'], 10000) for r in m1]):.2f} / x{st.mean([min(r['tenir7'], 10000) for r in m2]):.2f}")
        t_lanc = min(r["ts"] for r in r7)
        for nom, lo, hi in (("heure 1", 0, 3600), ("heures 2-24", 3600, 86400), ("jour 2", 86400, 172800), ("jour 3", 172800, 259200)):
            rs = [r for r in r7 if lo <= r["ts"] - t_lanc < hi]
            if rs:
                L.append(f"  {nom} (depuis le 1er pool de la fenêtre) : x10 {part(rs, 10)}")
        uni = [r for r in r7 if cre[r['createur']] == 1]
        ser = [r for r in r7 if cre[r['createur']] >= 3]
        if uni:
            L.append(f"  x10 créateur unique : {part(uni, 10)} ; en série : {part(ser, 10) if ser else 'n/a'}")
        mass = {u for u, n in usi.items() if n > 1000}
        if mass:
            L.append(f"  x10 usine de masse (>1000) : {part([r for r in r7 if r['usine'] in mass], 10)} ; autres : {part([r for r in r7 if r['usine'] not in mass], 10) if [r for r in r7 if r['usine'] not in mass] else 'n/a'}")
    imp = [r["imp110"] for r in res if r["imp110"] is not None]
    if imp:
        L.append(f"Impact médian à l'entrée : 110 $ {100 * st.median(imp):.1f} % ; 450 $ {100 * st.median([r['imp450'] for r in res if r['imp450'] is not None]):.1f} %")
    pieges = [r for r in res if r["n_ach24"] >= 5 and r["n_ven24"] == 0]
    L.append(f"Ventes bloquées probables (>= 5 achats, 0 vente >= 5 $ en 24 h) : {len(pieges)} sur {len(res)}")
    L.append(f"Transactions de swap dans les blocs 0 à +2 (médiane par pool) : {st.median([r['bots_bloc_0_2'] for r in res]):.0f}")
    return L


if __name__ == "__main__":
    main()
