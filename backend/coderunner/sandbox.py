"""
Sandboxed code execution for CodeSphere.

Every submission gets its own temporary work directory, and every compile
step and every test-case run happens inside a fresh, throw-away Docker
container started from the runner image (see ../../sandbox/Dockerfile):

    docker run --rm -i
        --network none                      no internet / no LAN access
        --memory 256m --memory-swap 256m    hard RAM cap (OOM kill -> MLE)
        --cpus 1                            one CPU core
        --pids-limit 128                    stops fork bombs
        --read-only --tmpfs /tmp            root filesystem is read-only
        --cap-drop ALL                      no Linux capabilities
        --security-opt no-new-privileges    no setuid escalation
        --user 65534:65534                  runs as 'nobody', never root
        -v <workdir>:/sandbox[:ro]          only this submission's files
        codesphere-runner judge-exec --time <TL> -- <run command>

`judge-exec` (judge_exec.py) runs the program, enforces the CPU-time limit
and reports exit code + CPU time, so verdicts and timings do not include
Docker's container start-up time. The container is removed as soon as the
program exits, so nothing a submission does survives to the next one.

SANDBOX_BACKEND=local runs the same wrapper as a plain subprocess with
setrlimit limits. It is only for local development on a machine without
Docker and must never be used in production.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

# --------------------------------------------------------------------------
# Language table: source file, compile command, run command.
# Each submission gets its own directory, so Java's fixed "Main.java" name
# can never collide between two users submitting at the same time.
# --------------------------------------------------------------------------
LANGUAGES = {
    "c": {
        "name": "C",
        "file": "main.c",
        "compile": ["gcc", "-O2", "-std=c17", "-o", "main", "main.c", "-lm"],
        "run": ["./main"],
    },
    "cpp": {
        "name": "C++",
        "file": "main.cpp",
        "compile": ["g++", "-O2", "-std=c++17", "-o", "main", "main.cpp"],
        "run": ["./main"],
    },
    "java": {
        "name": "Java",
        "file": "Main.java",
        "compile": ["javac", "-J-Xmx192m", "-J-XX:+UseSerialGC", "Main.java"],
        "run": ["java", "-Xmx192m", "-Xss64m", "-XX:+UseSerialGC", "-cp", ".", "Main"],
    },
    "py": {
        "name": "Python",
        "file": "main.py",
        "compile": None,
        "run": ["python3", "-B", "main.py"],
    },
    "js": {
        "name": "JavaScript",
        "file": "main.js",
        "compile": None,
        "run": ["node", "--max-old-space-size=192", "main.js"],
    },
}

# Verdicts for a single execution.
OK = "OK"
COMPILATION_ERROR = "Compilation Error"
RUNTIME_ERROR = "Runtime Error"
TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
SYSTEM_ERROR = "System Error"

META_MARKER = "@@CODESPHERE_META "  # printed by judge_exec.py
# Out-of-memory messages from the C++ runtime, CPython, the JVM and Node.
MEMORY_HINTS = ("std::bad_alloc", "MemoryError", "OutOfMemoryError", "heap out of memory")


@dataclass
class ExecResult:
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    time_ms: int = 0

    @property
    def ok(self) -> bool:
        return self.status == OK

    def display(self) -> str:
        """Text shown to the user after a Run."""
        if self.ok:
            return self.stdout
        return f"{self.status}\n{(self.stderr or '').strip()}".strip()


def _cfg(name, default):
    return getattr(settings, name, default)


def _truncate(data: bytes, limit: int) -> str:
    text = (data or b"").decode("utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n... (output truncated)"
    return text


class Sandbox:
    """
    One Sandbox == one submission's work directory.

        with Sandbox(code, "cpp") as box:
            compiled = box.compile()
            if compiled.ok:
                result = box.run(input_text)
    """

    def __init__(self, code: str, language: str):
        if language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        self.language = language
        self.spec = LANGUAGES[language]
        self.code = code or ""
        self.backend = _cfg("SANDBOX_BACKEND", "docker")
        self.image = _cfg("SANDBOX_IMAGE", "codesphere-runner:latest")
        self.time_limit = float(_cfg("SANDBOX_TIME_LIMIT", 2))
        self.compile_time_limit = float(_cfg("SANDBOX_COMPILE_TIME_LIMIT", 20))
        self.memory_mb = int(_cfg("SANDBOX_MEMORY_MB", 256))
        self.max_output = int(_cfg("SANDBOX_MAX_OUTPUT", 64 * 1024))
        self.root = Path(_cfg("SANDBOX_WORK_DIR", Path(settings.BASE_DIR) / "sandbox_runs"))
        self.workdir: Path | None = None

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.workdir = self.root / uuid.uuid4().hex
        self.workdir.mkdir()
        # The sandbox runs as 'nobody', which must be able to write the
        # compiled binary here during the compile step.
        os.chmod(self.workdir, 0o777)
        src = self.workdir / self.spec["file"]
        src.write_text(self.code)
        os.chmod(src, 0o644)
        return self

    def __exit__(self, *exc):
        if self.workdir is not None:
            shutil.rmtree(self.workdir, ignore_errors=True)

    # -- public API ----------------------------------------------------------
    def compile(self) -> ExecResult:
        if not self.spec["compile"]:
            return ExecResult(OK)
        res = self._exec(self.spec["compile"], b"", self.compile_time_limit, writable=True)
        if res.status == OK:
            return res
        if res.status == SYSTEM_ERROR:
            return res
        if res.status == TIME_LIMIT_EXCEEDED:
            return ExecResult(COMPILATION_ERROR, stderr="Compilation timed out", time_ms=res.time_ms)
        return ExecResult(COMPILATION_ERROR, stderr=res.stderr or res.stdout, exit_code=res.exit_code)

    def run(self, input_text: str) -> ExecResult:
        return self._exec(self.spec["run"], (input_text or "").encode(), self.time_limit, writable=False)

    # -- internals -----------------------------------------------------------
    def _exec(self, cmd, stdin: bytes, time_limit: float, writable: bool) -> ExecResult:
        if self.backend == "docker":
            return self._exec_docker(cmd, stdin, time_limit, writable)
        if self.backend == "local":
            return self._exec_local(cmd, stdin, time_limit)
        return ExecResult(SYSTEM_ERROR, stderr=f"Unknown SANDBOX_BACKEND '{self.backend}'")

    @staticmethod
    def _wrapper_args(time_limit: float, mem_mb: int):
        return ["--time", str(time_limit), "--mem", str(mem_mb), "--"]

    def _exec_docker(self, cmd, stdin, time_limit, writable) -> ExecResult:
        name = f"codesphere-run-{uuid.uuid4().hex[:12]}"
        mount = f"{self.workdir}:/sandbox" + ("" if writable else ":ro")
        docker_cmd = [
            "docker", "run", "--rm", "-i",
            "--name", name,
            "--network", "none",
            "--memory", f"{self.memory_mb}m",
            "--memory-swap", f"{self.memory_mb}m",
            "--cpus", "1",
            "--pids-limit", "128",
            "--read-only",
            "--tmpfs", "/tmp:rw,exec,size=64m",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--user", "65534:65534",
            "-e", "HOME=/tmp",
            "-v", mount,
            "-w", "/sandbox",
            self.image,
            # Memory is enforced by the container's cgroup, so --mem 0 here.
            "judge-exec", *self._wrapper_args(time_limit, 0), *cmd,
        ]
        try:
            proc = subprocess.run(docker_cmd, input=stdin, capture_output=True,
                                  timeout=time_limit * 2 + 30)
        except subprocess.TimeoutExpired:
            # judge-exec kills the program long before this; this only stops
            # a wedged container from blocking a web worker forever.
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)
            return ExecResult(TIME_LIMIT_EXCEEDED, time_ms=int(time_limit * 1000))
        except FileNotFoundError:
            return ExecResult(SYSTEM_ERROR, stderr="Docker CLI not found on the judge server")

        if proc.returncode == 125:  # docker itself failed: image missing, daemon down...
            return ExecResult(SYSTEM_ERROR, stderr=proc.stderr.decode(errors="replace"))
        return self._parse(proc, time_limit)

    def _exec_local(self, cmd, stdin, time_limit) -> ExecResult:
        """Development fallback: same wrapper as a plain subprocess. NOT isolated."""
        # The JVM and V8 reserve far more virtual memory than they use, so an
        # address-space limit would break them; only C/C++/Python get one.
        mem = self.memory_mb if self.language in ("c", "cpp", "py") else 0
        wrapper = [sys.executable, str(Path(__file__).with_name("judge_exec.py"))]
        try:
            proc = subprocess.run([*wrapper, *self._wrapper_args(time_limit, mem), *cmd],
                                  input=stdin, capture_output=True, cwd=self.workdir,
                                  timeout=time_limit * 2 + 30)
        except subprocess.TimeoutExpired:
            return ExecResult(TIME_LIMIT_EXCEEDED, time_ms=int(time_limit * 1000))
        return self._parse(proc, time_limit)

    def _parse(self, proc, time_limit) -> ExecResult:
        stdout = _truncate(proc.stdout, self.max_output)
        raw_err = (proc.stderr or b"").decode("utf-8", errors="replace")
        meta = None
        head, sep, tail = raw_err.rpartition(META_MARKER)
        if sep:
            try:
                meta = json.loads(tail.strip().splitlines()[0])
                raw_err = head.rstrip("\n")
            except (ValueError, IndexError):
                meta = None
        stderr = raw_err[-self.max_output:]

        if meta is None:
            # The whole container was OOM-killed (wrapper included).
            if proc.returncode == 137:
                return ExecResult(MEMORY_LIMIT_EXCEEDED, stdout, stderr, 137)
            return ExecResult(SYSTEM_ERROR, stdout, stderr or "sandbox produced no result", proc.returncode)

        code, sig, cpu_ms = meta["exit"], meta["signal"], meta["cpu_ms"]
        time_ms = min(cpu_ms, int(time_limit * 1000))
        if code == 127 and "judge-exec: cannot start" in stderr:
            return ExecResult(SYSTEM_ERROR, stdout, stderr, code)
        if meta["timed_out"]:
            return ExecResult(TIME_LIMIT_EXCEEDED, stdout, stderr, code, int(time_limit * 1000))
        if sig == 9 or any(h in stderr for h in MEMORY_HINTS):
            return ExecResult(MEMORY_LIMIT_EXCEEDED, stdout, stderr, code, time_ms)
        if code != 0:
            return ExecResult(RUNTIME_ERROR, stdout, stderr, code, time_ms)
        return ExecResult(OK, stdout, stderr, code, time_ms)


# --------------------------------------------------------------------------
# Judging helpers
# --------------------------------------------------------------------------
def normalize(text: str) -> str:
    """Ignore trailing spaces, trailing blank lines and Windows line endings."""
    text = (text or "").replace("\r", "").strip()
    return "\n".join(" ".join(line.split()) for line in text.split("\n"))


def run_once(code: str, language: str, input_text: str) -> ExecResult:
    """Compile (if needed) and run once on custom input: the Run button."""
    with Sandbox(code, language) as box:
        compiled = box.compile()
        if not compiled.ok:
            return compiled
        return box.run(input_text)


@dataclass
class JudgeResult:
    verdict: str
    message: str = ""
    max_time_ms: int = 0
    passed: int = 0
    total: int = 0


def judge(code: str, language: str, tests) -> JudgeResult:
    """
    Compile once, then run every (input, expected_output) pair in its own
    container. Stops at the first failing test, like Codeforces.
    """
    tests = list(tests)
    if not tests:
        return JudgeResult("No Test Cases found")
    with Sandbox(code, language) as box:
        compiled = box.compile()
        if not compiled.ok:
            return JudgeResult(compiled.status, compiled.stderr[-4000:], total=len(tests))
        max_time = 0
        for i, (input_text, expected) in enumerate(tests, start=1):
            res = box.run(input_text)
            max_time = max(max_time, res.time_ms)
            if res.status == SYSTEM_ERROR:
                return JudgeResult(SYSTEM_ERROR, res.stderr[-4000:], max_time, i - 1, len(tests))
            if not res.ok:
                return JudgeResult(f"{res.status} on test {i}", res.stderr[-4000:], max_time, i - 1, len(tests))
            if normalize(res.stdout) != normalize(expected):
                return JudgeResult(f"Wrong Answer on test {i}", "", max_time, i - 1, len(tests))
        return JudgeResult("Accepted", "", max_time, len(tests), len(tests))
