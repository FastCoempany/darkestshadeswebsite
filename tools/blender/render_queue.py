#!/usr/bin/env python3
"""The render queue (DRAWER-WALL.md, The render queue): resumable render jobs, one frame (or one wall) per job, from
a jobs file in work/queue/; each job skipped when its outputs exist; run at nice 19 in the background, in chunks
under a time limit; one line per finished job and one per failure.

    python3 tools/blender/render_queue.py add d3 wall-portrait-lit -- python3 tools/blender/drawer_wall.py wall --layout portrait --variant lit
        --outputs work/wall/portrait-black-relief-lit.png
    python3 tools/blender/render_queue.py add d3 seq-base-007 --outputs work/wall/seq/base/007.png -- python3 tools/blender/drawer_wall.py sequence --only 7
    python3 tools/blender/render_queue.py run d3 --minutes 95        # a chunk: stops starting jobs after 95 minutes
    python3 tools/blender/render_queue.py status d3
    python3 tools/blender/render_queue.py clear d3

A jobs file is work/queue/<name>.json: a list of {id, cmd, outputs, done, error, tools}. `run` takes jobs in order,
skips a job whose outputs all exist and verify (a readable image, parsable JSON; and marks it done), re-runs a job
marked done whose output has gone, runs the rest one at a time through `nice -n 19`, writes a log per job in
work/queue/log/<name>-<id>.log, and exits 0 when every job is done, 2 when the chunk's time ran out with jobs left,
1 when a job failed (it goes on to the next job; a failed job is retried on the next run). Each job carries a stamp
of the tool code it was rendered with; `status` names the jobs rendered with other code than today's.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
QUEUE = ROOT / "work" / "queue"


def load(name):
    p = QUEUE / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else []


def save(name, jobs):
    QUEUE.mkdir(parents=True, exist_ok=True)
    (QUEUE / f"{name}.json").write_text(json.dumps(jobs, indent=1))


TOOLS = ["tools/blender/drawer_wall.py", "tools/blender/frame3d.py", "tools/blender/frame_texture.py", "tools/photo/grade_scene.py"]


def tools_hash():
    """A stamp of the tool code a job is rendered with: a job whose stamp differs from today's was rendered by other
    code (the queue says so, and leaves the decision to re-render to `clear` and `add`)."""
    h = hashlib.sha1()
    for t in TOOLS:
        q = ROOT / t
        if q.exists():
            h.update(q.read_bytes())
    return h.hexdigest()[:12]


def output_ok(rel):
    """An output exists and verifies: a readable image, parsable JSON, a non-trivial HDR or EXR."""
    p = ROOT / rel
    if not p.exists() or p.stat().st_size == 0:
        return False
    ext = p.suffix.lower()
    try:
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".avif"):
            from PIL import Image
            if ext == ".avif":
                import pillow_avif  # noqa: F401
            with Image.open(p) as im:
                im.verify()
        elif ext == ".json":
            json.loads(p.read_text())
        elif ext in (".hdr", ".exr"):
            return p.stat().st_size > 1024
    except Exception:
        return False
    return True


def outputs_ok(job):
    return all(output_ok(o) for o in job["outputs"])


def cmd_add(a):
    jobs = load(a.queue)
    jobs = [j for j in jobs if j["id"] != a.id]
    jobs.append({"id": a.id, "cmd": a.command, "outputs": a.outputs, "done": False, "error": None, "tools": tools_hash()})
    save(a.queue, jobs)
    print(f"{a.queue}: {len(jobs)} jobs ({a.id} added)")


def cmd_status(a):
    jobs = load(a.queue)
    done = sum(1 for j in jobs if outputs_ok(j))
    failed = [j["id"] for j in jobs if j.get("error") and not outputs_ok(j)]
    stale = [j["id"] for j in jobs if outputs_ok(j) and j.get("tools") and j["tools"] != tools_hash()]
    print(f"{a.queue}: {done}/{len(jobs)} done, {len(failed)} failed{': ' + ', '.join(failed) if failed else ''}")
    if stale:
        print(f"{a.queue}: {len(stale)} done with other tool code than today's (clear and add to re-render): {', '.join(stale[:6])}{'…' if len(stale) > 6 else ''}")
    try:
        for j in jobs:
            state = "done" if outputs_ok(j) else ("failed" if j.get("error") else "left")
            print(f"  {state:6s} {j['id']}  {j.get('seconds', '')}")
    except BrokenPipeError:
        pass


def cmd_clear(a):
    p = QUEUE / f"{a.queue}.json"
    if p.exists():
        p.unlink()
    print(f"{a.queue}: cleared")


def cmd_run(a):
    jobs = load(a.queue)
    if not jobs:
        print(f"{a.queue}: no jobs")
        return 0
    (QUEUE / "log").mkdir(parents=True, exist_ok=True)
    start = time.time()
    limit = a.minutes * 60
    failed = 0
    left = 0
    stamp = tools_hash()
    for j in jobs:
        if outputs_ok(j):
            if not j["done"]:
                j["done"] = True
                save(a.queue, jobs)
            continue
        if j["done"]:
            print(f"redo   {j['id']}  (marked done, but an output is missing or does not read)", flush=True)
            j["done"] = False
        if time.time() - start > limit:
            left += 1
            continue
        log = QUEUE / "log" / f"{a.queue}-{j['id']}.log"
        t = time.time()
        with open(log, "w") as f:
            r = subprocess.run(["nice", "-n", "19", *j["cmd"]], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        secs = int(time.time() - t)
        ok = r.returncode == 0 and outputs_ok(j)
        j["seconds"] = secs
        if ok:
            j["done"], j["error"], j["tools"] = True, None, stamp
            print(f"done   {j['id']}  {secs}s", flush=True)
        else:
            j["error"] = f"exit {r.returncode}" if r.returncode else "outputs missing"
            failed += 1
            print(f"FAILED {j['id']}  {secs}s  ({j['error']}; see {log.relative_to(ROOT)})", flush=True)
        save(a.queue, jobs)
    done = sum(1 for j in jobs if j["done"])
    print(f"{a.queue}: {done}/{len(jobs)} done, {failed} failed this run, {left} left for the next chunk ({int(time.time() - start)}s)")
    return 1 if failed else (2 if left else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("queue")
    p.add_argument("id")
    p.add_argument("--outputs", nargs="+", required=True, help="files, relative to the repo root, that the job must leave behind")
    p.add_argument("command", nargs="*", help="the command, after --")
    p = sub.add_parser("run")
    p.add_argument("queue")
    p.add_argument("--minutes", type=float, default=95.0)
    p = sub.add_parser("status")
    p.add_argument("queue")
    p = sub.add_parser("clear")
    p.add_argument("queue")
    a = ap.parse_args()
    if a.cmd == "add":
        a.command = [c for c in a.command if c != "--"]
        if not a.command:
            ap.error("add needs a command after --")
    code = {"add": cmd_add, "run": cmd_run, "status": cmd_status, "clear": cmd_clear}[a.cmd](a)
    raise SystemExit(code or 0)


if __name__ == "__main__":
    main()
