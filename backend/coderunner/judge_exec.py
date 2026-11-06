#!/usr/bin/env python3
"""
judge-exec: runs ONE program with limits and reports how it went.

It is copied into the runner image as /usr/local/bin/judge-exec and is the
command every sandbox container executes:

    judge-exec --time 2 [--mem 256] -- ./main

* stdin / stdout are passed straight through to the program.
* The program's stderr is captured, then the wrapper prints one meta line
  at the very end of stderr:

      @@CODESPHERE_META {"exit": 0, "signal": 0, "cpu_ms": 12, "wall_ms": 15, "timed_out": false}

  The Django side parses that line to decide the verdict, so the measured
  time is the program's own CPU time, not Docker's start-up time.

Only the Python standard library is used, so it runs in the slim runner
image and on a developer laptop alike.
"""
import argparse
import json
import os
import resource
import signal
import subprocess
import sys
import time

META = "@@CODESPHERE_META "


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", type=float, required=True, help="CPU time limit in seconds")
    parser.add_argument("--mem", type=int, default=0, help="address-space limit in MB (0 = none)")
    parser.add_argument("--fsize", type=int, default=16, help="max file size written, MB")
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        print("judge-exec: no command", file=sys.stderr)
        return 2

    cpu_limit = max(1, int(args.time + 0.999))

    def limits():
        os.setsid()  # own process group, so a timeout kills every child
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 1))
        fsize = args.fsize * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        if args.mem:
            mem = args.mem * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))

    # Wall-clock limit is generous (programs blocked on I/O or sleeping use
    # no CPU); the CPU limit is the one that decides TLE.
    wall_limit = args.time * 2 + 1
    start = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, preexec_fn=limits)
    except OSError as exc:
        sys.stderr.write(f"judge-exec: cannot start {cmd[0]}: {exc}\n")
        sys.stderr.write(META + json.dumps({"exit": 127, "signal": 0, "cpu_ms": 0,
                                            "wall_ms": 0, "timed_out": False}) + "\n")
        return 0
    try:
        _, err = proc.communicate(timeout=wall_limit)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        _, err = proc.communicate()
    wall_ms = int((time.monotonic() - start) * 1000)
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_ms = int((usage.ru_utime + usage.ru_stime) * 1000)

    rc = proc.returncode
    sig = -rc if rc < 0 else 0
    if sig == signal.SIGXCPU or cpu_ms > args.time * 1000:
        timed_out = True

    sys.stderr.buffer.write(err[-65536:] if err else b"")
    sys.stderr.write("\n" + META + json.dumps({
        "exit": rc if rc >= 0 else 128 + sig,
        "signal": sig,
        "cpu_ms": cpu_ms,
        "wall_ms": wall_ms,
        "timed_out": timed_out,
    }) + "\n")
    sys.stderr.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
