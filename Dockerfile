FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    make \
    cmake \
    flex \
    bison \
    python3 \
    perl \
    bc \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 https://github.com/AI-Planning/pddl-generators.git

# Build domains in two passes:
#  1) Top-level: run `make` (default target) for every top-level domain whose
#     first Makefile target is NOT `test:` (skip pure-script domains).
#  2) Sub-projects: also build any nested Makefile (e.g. trucks/adl2strips/) that
#     the parent's default target doesn't build but the runtime needs.
RUN set +e; \
    for d in /build/pddl-generators/*/; do \
        [ -f "$d/Makefile" ] || continue; \
        has_source=$(ls "$d"*.c "$d"*.cc "$d"*.cpp "$d"*.cxx 2>/dev/null | head -1); \
        first_target=$(grep -E '^[a-zA-Z][^:]*:' "$d/Makefile" | head -1 | sed 's/[: ].*//'); \
        if [ -z "$has_source" ] && [ "$first_target" = "test" ]; then \
            echo "SKIP-NOCOMPILE $(basename $d)"; \
        else \
            (cd "$d" && make -j"$(nproc)" 2>&1 >/dev/null) \
                && echo "BUILT $(basename $d)" \
                || echo "FAILED $(basename $d)"; \
        fi; \
    done; \
    find /build/pddl-generators -mindepth 3 -name Makefile -type f | while read mk; do \
        subdir=$(dirname "$mk"); \
        sub_target=$(grep -E '^[a-zA-Z][^:]*:' "$mk" | head -1 | sed 's/[: ].*//'); \
        [ "$sub_target" = "test" ] && continue; \
        [ -z "$sub_target" ] && continue; \
        (cd "$subdir" && make -j"$(nproc)" 2>&1 >/dev/null) \
            && echo "BUILT-SUB ${subdir#/build/pddl-generators/}" \
            || echo "FAILED-SUB ${subdir#/build/pddl-generators/}"; \
    done; \
    true


FROM python:3.13-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    perl \
    libstdc++6 \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Some upstream generator scripts hard-code `#!/usr/bin/python3`. The slim base
# only ships /usr/local/bin/python3, so symlink to keep those shebangs working.
RUN ln -sf /usr/local/bin/python3 /usr/bin/python3 \
 && ln -sf /usr/local/bin/python3 /usr/bin/python

RUN pip install --no-cache-dir uv numpy z3-solver

COPY --from=builder /build/pddl-generators /opt/pddl-generators

# Install workspace packages. Order matters: pddl-dataset and pddl-simulator
# are both runtime deps of pddl-cli, so install them first.
COPY packages/pddl-dataset /opt/pddl-dataset
RUN pip install --no-cache-dir /opt/pddl-dataset

COPY packages/pddl-simulator /opt/pddl-simulator
RUN pip install --no-cache-dir /opt/pddl-simulator

COPY pddl-cli /opt/pddl-cli
RUN pip install --no-cache-dir /opt/pddl-cli

ENV PDDL_GENERATORS_DIR=/opt/pddl-generators
WORKDIR /work
ENTRYPOINT ["pddl-cli"]
