#!/usr/bin/env python3
"""Pull single files out of the 1.48 GB DARKESTSHADES.zip release asset without downloading it.

Reads the zip's central directory with HTTP range requests (zip64 aware), then fetches only the
matching members. Needs a GitHub token with read access to FastCoempany/darkestshades in GH_TOKEN.

    python3 tools/photo/zipget.py --out work/originals "Lighbox shots/IMG_3596\\.jpg$"
    python3 tools/photo/zipget.py --list "Lighbox shots/"          # list matching members only
    python3 tools/photo/zipget.py --picks content/photography/lightbox-angle-set.json --frames F08 --out work/originals

Files land in --out with their base name (IMG_3596.jpg). work/ is git-ignored.
"""
import argparse
import json
import os
import pathlib
import re
import struct
import urllib.error
import urllib.request
import zlib

REPO = "FastCoempany/darkestshades"
ASSET_ID = 510463250  # release "darkestshades" -> DARKESTSHADES.zip


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(newurl, code, msg, headers, fp)


def signed_url(token):
    """Ask the GitHub API for the asset; it answers with a short-lived signed URL (not followed,
    so the token never goes to the storage host)."""
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/assets/{ASSET_ID}",
                                 headers={"Accept": "application/octet-stream", "Authorization": f"token {token}"})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        opener.open(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return e.headers["Location"]
        raise
    raise RuntimeError("expected a redirect to the asset's storage URL")


class Zip:
    def __init__(self, url):
        self.url = url
        self.size = int(urllib.request.urlopen(urllib.request.Request(url, headers={"Range": "bytes=0-0"}), timeout=60)
                        .headers["Content-Range"].split("/")[1])
        self.entries = self._central_directory()

    def rng(self, a, b):
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={a}-{b}"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()

    def _central_directory(self):
        tail = self.rng(self.size - 70000, self.size - 1)
        i = tail.rfind(b"PK\x05\x06")
        _, _, _, _, _, cd_size, cd_off, _ = struct.unpack("<IHHHHIIH", tail[i:i + 22])
        if cd_off == 0xFFFFFFFF:
            j = tail.rfind(b"PK\x06\x07")
            _, _, z64_off, _ = struct.unpack("<IIQI", tail[j:j + 20])
            z = self.rng(z64_off, z64_off + 55)
            cd_size, cd_off = struct.unpack("<IQHHIIQQQQ", z)[8:10]
        cd = self.rng(cd_off, cd_off + cd_size - 1)
        p, out = 0, []
        while p < len(cd) and cd[p:p + 4] == b"PK\x01\x02":
            f = struct.unpack("<IHHHHHHIIIHHHHHII", cd[p:p + 46])
            comp, csize, usize, nlen, xlen, klen, lho = f[4], f[8], f[9], f[10], f[11], f[12], f[16]
            name = cd[p + 46:p + 46 + nlen].decode("utf-8", "replace")
            extra = cd[p + 46 + nlen:p + 46 + nlen + xlen]
            q = 0
            while q + 4 <= len(extra):
                hid, hsz = struct.unpack("<HH", extra[q:q + 4])
                body = extra[q + 4:q + 4 + hsz]
                if hid == 1:  # zip64 extra field
                    k, vals = 0, []
                    for want in (usize == 0xFFFFFFFF, csize == 0xFFFFFFFF, lho == 0xFFFFFFFF):
                        if want:
                            vals.append(struct.unpack("<Q", body[k:k + 8])[0]); k += 8
                        else:
                            vals.append(None)
                    usize = vals[0] or usize
                    csize = vals[1] or csize
                    lho = vals[2] if vals[2] is not None else lho
                q += 4 + hsz
            out.append((name, comp, csize, usize, lho))
            p += 46 + nlen + xlen + klen
        return out

    def read(self, entry):
        name, comp, csize, usize, lho = entry
        h = self.rng(lho, lho + 29)
        nlen, xlen = struct.unpack("<HH", h[26:30])
        start = lho + 30 + nlen + xlen
        data = self.rng(start, start + csize - 1)
        return zlib.decompress(data, -15) if comp == 8 else data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="*", help="regexes matched against member paths")
    ap.add_argument("--out", default="work/originals")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--picks", help="lightbox-angle-set.json: fetch the picks (and alternates with --alternates)")
    ap.add_argument("--frames", default="", help="comma-separated frame IDs for --picks (default: all)")
    ap.add_argument("--alternates", action="store_true")
    a = ap.parse_args()

    pats = list(a.patterns)
    if a.picks:
        sets = json.loads(pathlib.Path(a.picks).read_text())["frames"]
        want = [f for f in sets if not a.frames or f in a.frames.split(",")]
        for f in want:
            names = [v for v in sets[f]["picks"].values() if v]
            if a.alternates:
                names += [n for vs in sets[f]["alternates"].values() for n in vs]
            pats += [rf"Lighbox shots/{n}\.jpg$" for n in names]

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("set GH_TOKEN to a token that can read FastCoempany/darkestshades")
    z = Zip(signed_url(token))
    hits = [e for e in z.entries if not e[0].endswith("/") and "__MACOSX" not in e[0]
            and any(re.search(p, e[0]) for p in pats)]
    if a.list:
        for e in hits:
            print(f"{e[3] / 1e6:8.2f} MB  {e[0]}")
        return
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for e in hits:
        dest = out / pathlib.Path(e[0]).name
        if dest.exists() and dest.stat().st_size == e[3]:
            continue
        dest.write_bytes(z.read(e))
        print(f"{e[3] / 1e6:6.2f} MB  {dest}")


if __name__ == "__main__":
    main()
