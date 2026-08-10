"""
Stack inspection script — run after `docker compose up -d`.

Checks:
  1. All services are reachable
  2. Tables/collections present in each store
  3. Row/document counts per table

Usage:
    python scripts/inspect_stack.py
"""

import sys
import textwrap


# ── colour helpers ────────────────────────────────────────────────────────────

GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ok   = lambda s: f"{GREEN}✓{RESET} {s}"
fail = lambda s: f"{RED}✗{RESET} {s}"
warn = lambda s: f"{YELLOW}!{RESET} {s}"
hdr  = lambda s: f"\n{BOLD}{s}{RESET}"


# ── result collector ──────────────────────────────────────────────────────────

class Report:
    def __init__(self):
        self.failures = []

    def success(self, msg):
        print(ok(msg))

    def error(self, msg):
        print(fail(msg))
        self.failures.append(msg)

    def warning(self, msg):
        print(warn(msg))


report = Report()


# ── 1. PostgreSQL ─────────────────────────────────────────────────────────────

print(hdr("PostgreSQL  (localhost:5432 / primeev_factory)"))

try:
    import psycopg2

    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="primeev_factory",
        user="primeev", password="primeev_dev",
        connect_timeout=5,
    )
    report.success("connected")

    cur = conn.cursor()

    # list tables
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [r[0] for r in cur.fetchall()]

    if not tables:
        report.error("no tables found — has datagen run?")
    else:
        print(f"  {len(tables)} tables found")

        # row counts
        counts = []
        for tbl in tables:
            cur.execute(f"SELECT count(*) FROM {tbl}")  # noqa: S608 — internal script
            counts.append((tbl, cur.fetchone()[0]))

        max_name = max(len(t) for t, _ in counts)
        total = 0
        for tbl, n in sorted(counts, key=lambda x: -x[1]):
            flag = "  " if n > 0 else warn("")
            print(f"  {flag}{tbl:<{max_name}}  {n:>10,}")
            total += n
        print(f"  {'TOTAL':<{max_name}}  {total:>10,}")

        empty = [t for t, n in counts if n == 0]
        if empty:
            report.warning(f"{len(empty)} empty tables: {', '.join(empty)}")
        else:
            report.success("all tables non-empty")

    cur.close()
    conn.close()

except Exception as exc:
    report.error(f"PostgreSQL unreachable — {exc}")


# ── 2. ClickHouse ─────────────────────────────────────────────────────────────

print(hdr("ClickHouse  (localhost:8123 / primeev_telemetry)"))

try:
    import clickhouse_connect

    ch = clickhouse_connect.get_client(
        host="localhost", port=8123,
        database="primeev_telemetry",
        username="default", password="",
        connect_timeout=5,
    )
    ch.ping()
    report.success("connected")

    rows = ch.query(
        "SELECT name FROM system.tables WHERE database = 'primeev_telemetry' ORDER BY name"
    )
    tables = [r[0] for r in rows.result_rows]

    if not tables:
        report.error("no tables found — has datagen run?")
    else:
        print(f"  {len(tables)} tables found")

        counts = []
        for tbl in tables:
            result = ch.query("SELECT count() FROM primeev_telemetry." + tbl)
            counts.append((tbl, result.result_rows[0][0]))

        max_name = max(len(t) for t, _ in counts)
        total = 0
        for tbl, n in sorted(counts, key=lambda x: -x[1]):
            flag = "  " if n > 0 else warn("")
            print(f"  {flag}{tbl:<{max_name}}  {n:>12,}")
            total += n
        print(f"  {'TOTAL':<{max_name}}  {total:>12,}")

        empty = [t for t, n in counts if n == 0]
        if empty:
            report.warning(f"{len(empty)} empty tables: {', '.join(empty)}")
        else:
            report.success("all tables non-empty")

    ch.close()

except Exception as exc:
    report.error(f"ClickHouse unreachable — {exc}")


# ── 3. ChromaDB ───────────────────────────────────────────────────────────────

print(hdr("ChromaDB  (localhost:8001)"))

try:
    import chromadb

    chroma = chromadb.HttpClient(host="localhost", port=8001)
    chroma.heartbeat()
    report.success("connected")

    collections = chroma.list_collections()

    if not collections:
        report.error("no collections found — has RAG indexing run?")
    else:
        print(f"  {len(collections)} collection(s) found")
        max_name = max(len(c.name) for c in collections)
        total = 0
        for col in sorted(collections, key=lambda c: -c.count()):
            n = col.count()
            flag = "  " if n > 0 else warn("")
            print(f"  {flag}{col.name:<{max_name}}  {n:>8,} chunks")
            total += n
        print(f"  {'TOTAL':<{max_name}}  {total:>8,} chunks")

        empty = [c.name for c in collections if c.count() == 0]
        if empty:
            report.warning(f"{len(empty)} empty collections: {', '.join(empty)}")
        else:
            report.success("all collections non-empty")

except Exception as exc:
    report.error(f"ChromaDB unreachable — {exc}")


# ── 4. Kafka ──────────────────────────────────────────────────────────────────

print(hdr("Kafka  (localhost:9092)"))

try:
    from confluent_kafka.admin import AdminClient

    admin = AdminClient({"bootstrap.servers": "localhost:9092", "socket.timeout.ms": 5000})
    metadata = admin.list_topics(timeout=5)
    report.success("connected")

    user_topics = sorted(
        t for t in metadata.topics if not t.startswith("__")
    )

    if not user_topics:
        report.warning("no user topics yet — simulator not started")
    else:
        print(f"  {len(user_topics)} topic(s)")
        for topic in user_topics:
            partitions = len(metadata.topics[topic].partitions)
            print(f"    {topic}  ({partitions} partition{'s' if partitions != 1 else ''})")
        report.success("topics present")

except Exception as exc:
    report.error(f"Kafka unreachable — {exc}")


# ── 5. FastAPI health ─────────────────────────────────────────────────────────

print(hdr("FastAPI  (localhost:8000)"))

try:
    import urllib.request

    with urllib.request.urlopen("http://localhost:8000/api/health", timeout=5) as resp:
        if resp.status == 200:
            report.success(f"healthy (HTTP {resp.status})")
        else:
            report.error(f"unhealthy (HTTP {resp.status})")

except Exception as exc:
    report.error(f"API unreachable — {exc}")


# ── Summary ───────────────────────────────────────────────────────────────────

print(hdr("Summary"))

if report.failures:
    print(f"\n{RED}{BOLD}{len(report.failures)} failure(s):{RESET}")
    for f in report.failures:
        print(f"  {RED}•{RESET} {f}")
    print(textwrap.dedent(f"""
  {YELLOW}Tip:{RESET} run `docker compose up -d` and wait ~2 min for datagen to seed,
  then re-run this script.
    """).rstrip())
    sys.exit(1)
else:
    print(f"\n{GREEN}{BOLD}All services up and data loaded.{RESET}\n")
    sys.exit(0)
