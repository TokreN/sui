"""Outils communs aux scripts du filon 1.

- Python 3.13, aucune clé, aucune dépendance hors bibliothèque standard.
- Cache .json sur disque (dossier CACHE_DIR, par défaut ./cache à côté du script).
- RPC lu dans la variable d'environnement RPC_URL (jamais dans le code).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.environ.get("CACHE_DIR", os.path.join(ICI, "cache"))
os.makedirs(CACHE_DIR, exist_ok=True)
UA = {"User-Agent": "filon1-recherche/1.0", "Accept": "application/json"}

_verrous: dict[str, threading.Lock] = {}
_dernier: dict[str, float] = {}
_verrou_global = threading.Lock()

# pauses minimales entre deux appels, par hôte (API gratuites)
PAUSES = {
    "api.geckoterminal.com": 2.2,  # ~30 appels/min
    "api.dexscreener.com": 0.25,
    "api.llama.fi": 0.15,
}


def _cle(url: str, corps: bytes | None) -> str:
    h = hashlib.sha1(url.encode() + (corps or b"")).hexdigest()[:20]
    return os.path.join(CACHE_DIR, f"{h}.json")


def _attendre(hote: str) -> None:
    pause = PAUSES.get(hote, 0.0)
    if not pause:
        return
    with _verrou_global:
        v = _verrous.setdefault(hote, threading.Lock())
    with v:
        reste = _dernier.get(hote, 0) + pause - time.time()
        if reste > 0:
            time.sleep(reste)
        _dernier[hote] = time.time()


def get_json(url: str, cache: bool = True, ttl: float | None = None, essais: int = 5):
    """GET JSON avec cache disque. ttl en secondes (None = cache permanent)."""
    chemin = _cle(url, None)
    if cache and os.path.exists(chemin):
        if ttl is None or time.time() - os.path.getmtime(chemin) < ttl:
            with open(chemin, encoding="utf-8") as f:
                return json.load(f)
    hote = url.split("/")[2]
    attente = 3.0
    for i in range(essais):
        _attendre(hote)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                donnees = json.loads(r.read().decode("utf-8"))
            if cache:
                with open(chemin, "w", encoding="utf-8") as f:
                    json.dump(donnees, f)
            return donnees
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 500, 502, 503, 504) and i < essais - 1:
                time.sleep(attente)
                attente *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if i < essais - 1:
                time.sleep(attente)
                attente *= 2
                continue
            raise
    return None


def rpc(methode: str, params: list, url: str | None = None, cache: bool = False, essais: int = 5):
    """Appel JSON-RPC. URL = RPC_URL (variable d'environnement) par défaut."""
    url = url or os.environ.get("RPC_URL")
    if not url:
        raise SystemExit("Mets l'URL du RPC dans la variable d'environnement RPC_URL.")
    corps = json.dumps({"jsonrpc": "2.0", "id": 1, "method": methode, "params": params}).encode()
    chemin = _cle(url + methode, corps)
    if cache and os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    attente = 2.0
    for i in range(essais):
        try:
            req = urllib.request.Request(url, data=corps, headers={**UA, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                rep = json.loads(r.read().decode("utf-8"))
            if "error" in rep:
                raise RuntimeError(f"RPC {methode}: {rep['error']}")
            res = rep["result"]
            if cache:
                with open(chemin, "w", encoding="utf-8") as f:
                    json.dump(res, f)
            return res
        except RuntimeError:
            raise
        except Exception:
            if i < essais - 1:
                time.sleep(attente)
                attente *= 2
                continue
            raise


def en_parallele(fonction, elements, fils: int = 6):
    """Applique fonction à chaque élément avec un pool de fils. Garde l'ordre."""
    with ThreadPoolExecutor(max_workers=fils) as ex:
        return list(ex.map(fonction, elements))


def ecrire_txt(nom: str, lignes: list[str]) -> str:
    chemin = os.path.join(ICI, nom)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    return chemin
