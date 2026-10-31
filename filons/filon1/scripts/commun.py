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


def rpc(methode: str, params: list, url: str | None = None, cache: bool = False, essais: int = 10):
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
                msg = str(rep["error"]).lower()
                limite = rep["error"].get("code") in (-32005, -32029, 429) or "rate" in msg or "too many" in msg or "timeout" in msg or "aborted" in msg
                if (limite and "range" not in msg or "invalid block range" in msg) and i < essais - 1:
                    time.sleep(attente)
                    attente = min(attente * 2, 30)
                    continue
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


_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B,
    0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088,
    0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1


def keccak256(donnees: bytes) -> bytes:
    """Keccak-256 (celui d'Ethereum, pas SHA3-256), en Python pur."""
    taux = 136
    d = bytearray(donnees) + b"\x01"
    while len(d) % taux:
        d += b"\x00"
    d[-1] |= 0x80
    A = [[0] * 5 for _ in range(5)]
    for bloc in range(0, len(d), taux):
        for i in range(taux // 8):
            A[i % 5][i // 5] ^= int.from_bytes(d[bloc + 8 * i: bloc + 8 * i + 8], "little")
        for rc in _RC:
            C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
            D = [C[(x - 1) % 5] ^ (((C[(x + 1) % 5] << 1) | (C[(x + 1) % 5] >> 63)) & _M) for x in range(5)]
            A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
            B = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    r = _ROT[x][y]
                    B[y][(2 * x + 3 * y) % 5] = ((A[x][y] << r) | (A[x][y] >> (64 - r))) & _M if r else A[x][y]
            A = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
            A[0][0] ^= rc
    out = b"".join(A[i % 5][i // 5].to_bytes(8, "little") for i in range(4))
    return out


def sujet(signature: str) -> str:
    """topic0 d'un événement, ex. sujet('Transfer(address,address,uint256)')."""
    return "0x" + keccak256(signature.encode()).hex()


def en_parallele(fonction, elements, fils: int = 6):
    """Applique fonction à chaque élément avec un pool de fils. Garde l'ordre."""
    with ThreadPoolExecutor(max_workers=fils) as ex:
        return list(ex.map(fonction, elements))


def ecrire_txt(nom: str, lignes: list[str]) -> str:
    chemin = os.path.join(ICI, nom)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    return chemin
