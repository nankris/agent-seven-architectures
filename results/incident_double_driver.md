# Incident: second confirmatory driver (18 Oct 2026)

- 07:31:25 UTC: the confirmatory driver (32 workers) was started on the VM automatically after the pilot finished
  (chained by an earlier session), i.e. ~7 min BEFORE the pilot amendment was committed (754d0d8, ~07:38 UTC).
  The amendment changed no hypothesis, prediction, margin or metric; pre-registration commit 6293f00 predates both.
- 07:39:47 UTC: a second driver (24 workers) was started by mistake on the same output file while the first was
  running (the JSONL then had 1,247 rows). Killed at 07:41:11 UTC (1,514 rows).
- Risk: the two drivers could run the same (arch, task, seed, condition) at once; V4/V7 share a checkpoint file per
  run id, and GPU load doubled (latency). Remedy (decided before looking at any confirmatory outcome):
  drop every row written after line 1,247 up to line 2,066 (the count at 07:44:34 UTC, kill + 3.4 min; the longest pilot run took 49 s),
  plus any duplicate keys, and re-run those jobs with a single driver. See scripts/clean_confirm.py.

## Update: VM lost, confirmatory run redone from scratch (18 Oct 2026)

- 07:57-08:05 UTC: the first driver finished (3,888 raw rows incl. 108 duplicate keys), the cleanup kept 3,069 rows
  and a single driver started re-running the 711 dropped jobs. Before any of these rows were copied off the VM,
  Colab reclaimed the runtime (all sessions on the account vanished, ~08:05 UTC). No confirmatory outcome had been
  looked at; nothing from that attempt survives or is used.
- 08:09 UTC: new L4 session b8-133; the full confirmatory run (T01-T60 x 3 seeds x 7 archs x 3 conditions,
  3,780 runs) is redone from scratch with ONE driver, 32 workers (same as the first driver), same code and server
  flags. The cleanup rule above is therefore moot; results/runs_confirm.jsonl is copied to the sandbox every few minutes.
