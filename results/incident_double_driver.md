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

## Update 2: second double-driver start on the new VM (18 Oct 2026)

- 08:27:53 UTC: after vLLM came up on the new VM, two launch chains (chain.log, chain2.log) each started a confirmatory
  driver on the same output file (PIDs 8699, 8709; both began from "0 done, 3780 to run").
- 08:31 UTC: found on resume (688 rows written, never copied off the VM, no outcomes looked at). Both drivers killed, the
  partial file moved to /content/exp133/discarded/ (not used), checkpoint dir wiped, and ONE driver started at
  08:31:47 UTC (32 workers, same code and flags). Every row in results/runs_confirm.jsonl comes from this single driver.

## Update 3: VM lost again mid-run; resumed from the saved rows (18 Oct 2026)

- ~08:46-09:09 UTC: Colab reclaimed the b8-133 runtime again while the single driver (started 08:31:47) was at ~2,231/3,780 rows.
  The last copy pulled to the sandbox (08:46 UTC) has 2,231 complete rows, all unique keys, all from that single driver.
- Resume (decided before looking at any confirmatory outcome): new L4 session, same code, model and server flags; the 2,231
  rows are uploaded and run_phase.py runs only the 1,549 missing (arch, task, seed, condition) jobs with ONE driver, 32
  workers, empty checkpoint dir. Runs in flight when the VM died left no row and are re-run from scratch.
- 09:17 UTC: the fresh VM installed vLLM 0.31.0, which rejects `disable_any_whitespace` unless the structured-output
  backend is named. Server flag changed to `{"backend": "xgrammar", "disable_any_whitespace": true}` (xgrammar is
  vLLM's default first-choice backend; same intent as before). Model, sampling, agent and scoring code unchanged.
  Rows written after this resume are tagged by file position (rows 2,232+ of runs_confirm.jsonl) so they can be
  compared with the first 2,231 as a sanity check.
