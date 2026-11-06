# CodeSphere runner image: the ONLY place user code is compiled and run.
# Build from the repository root:
#   docker build -f sandbox/Dockerfile -t codesphere-runner .
#
# Every submission is executed in a fresh container from this image with
# no network, a read-only root filesystem, capped memory/CPU/processes and
# as the unprivileged 'nobody' user (see backend/coderunner/sandbox.py).
FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        gcc g++ libc6-dev \
        openjdk-17-jdk-headless \
        python3 \
        nodejs \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Small wrapper that enforces the CPU-time limit and reports exit code/time.
COPY backend/coderunner/judge_exec.py /usr/local/bin/judge-exec
RUN chmod 755 /usr/local/bin/judge-exec

USER 65534:65534
WORKDIR /sandbox
CMD ["judge-exec", "--help"]
