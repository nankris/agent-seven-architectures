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
