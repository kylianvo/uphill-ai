# Glibc-based Metabase image.
#
# The official metabase/metabase image is Alpine (musl libc) on every
# architecture it publishes. The DuckDB Metabase driver (installed by the
# metabase-driver-init service into the shared /plugins volume) bundles a
# native lib that statically links jemalloc; loading it under musl crashes
# the JVM with SIGSEGV (`malloc_init_hard`, and on arm64 also
# `init_have_lse_atomics`) as soon as Metabase tries to connect to a DuckDB
# database. Neither `libstdc++` nor `gcompat` fixes it -- it's a musl/jemalloc
# ABI incompatibility, not a missing-library problem.
#
# Fix: re-host Metabase's own app directory (just a JAR + a POSIX shell
# script, nothing Alpine-specific) on a Debian-based JRE image, which uses
# glibc and doesn't trigger the bug.
# Pinned (not `latest`): the DuckDB community driver (motherduckdb/metabase_
# duckdb_driver) is broken against Metabase >= 0.63's new "transforms /
# workspaces" connection-pool architecture -- Metabase now injects a
# `connection-pool-type` key into the JDBC connection details for every
# sql-jdbc driver, and DuckDB's JDBC driver validates ALL properties
# strictly, so it 400s with "The following options were not recognized:
# connection-pool-type" on every single query and even the initial
# "add database" test-connection call. The upstream fix
# (motherduckdb/metabase_duckdb_driver#104) is merged to their main branch
# but not yet in a tagged release.
#
# Pinned specifically to v0.62.3.3 (not just "any pre-0.63 tag" like the
# earlier v0.60.15 pin) because prod's Metabase app-db schema was created by
# that exact version -- Metabase's own migration system refuses to boot an
# older binary against a newer schema ("Downgrade detected", verified live
# 2026-08-19). Both v0.62.3.3 and v0.60.15 predate the 0.63 architecture
# change, so the driver-compatibility reasoning above still holds; the schema
# match is the only reason this pin is more specific than "any pre-0.63 tag".
# If prod's Metabase is ever upgraded, this pin must move with it.
FROM metabase/metabase:v0.62.3.3 AS metabase-src

FROM eclipse-temurin:21-jre-jammy
RUN apt-get update \
    && apt-get install -y --no-install-recommends fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
COPY --from=metabase-src /app /app
# Deliberately NOT `WORKDIR /app`: Metabase resolves its default plugins dir
# as "plugins" relative to the process's cwd, and the official image's
# WORKDIR is `/` (root) so that resolves to `/plugins` -- matching the
# `metabase_plugins:/plugins` volume mount in docker-compose.yml. Setting
# WORKDIR to /app here made it resolve to /app/plugins instead, which is
# empty, so the DuckDB driver jar (dropped into /plugins by the
# metabase-driver-init service) silently failed to load.
EXPOSE 3000
ENTRYPOINT ["/bin/bash", "/app/run_metabase.sh"]
