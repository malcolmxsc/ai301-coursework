# Unit 2 — Claim and Reproduce

Path: `beat-1-sandbox/unit-2/reproduction.md`

## Your identity upstream

**GitHub username**

malcolmxsc

## Posted upstream

**Claim comment**

https://github.com/codepath/pathreview-ai301-fa26-s1/issues/33#issuecomment-6405657640

I am investigating #33, where two review requests for the same profile may enter the agent loop together and read stale profile state. I will trace `api/routes/reviews.py` and `core/services/review_service.py`, then try concurrent same-profile requests and compare their execution with sequential requests. I will post a reproduction report with the tested commit, environment, runnable steps, and observed output, including any limits if I cannot reproduce the behavior.

I used AI assistance to prepare this investigation and write-up.

**Reproduction comment**

https://github.com/codepath/pathreview-ai301-fa26-s1/issues/33#issuecomment-6405787749

Investigation of #33: **I could not reproduce inconsistent review output in the current placeholder implementation.** A controlled scheduling probe did show the missing same-profile serialization: both requests reached the agent stage before either exited. That probe does not establish a stale read or a lost update.

**Environment and code state**

- Fork: `malcolmxsc/pathreview-ai301-fa26-s1`, commit `f89c06fc3ff292df2a04a39ac51319d32a76b779`; application source unchanged (`git status --short` was empty).
- macOS 27.0.1, Apple Silicon arm64; Python 3.12.13; Docker client 29.5.0 / server 29.2.1 via Colima; Compose 5.1.1.
- PostgreSQL 16.15 (`postgres:16-alpine`, host port 5433) and Redis 7.4.11 (`redis:7-alpine`) healthy. The compose Chroma 0.4.22 container exited with `AttributeError: np.float_ was removed in the NumPy 2.0 release`; it was unavailable during this run. The tested review path uses placeholder RAG code and did not call it.
- FastAPI 0.162.0, Starlette 1.10.0, SQLAlchemy 2.1.6, asyncpg 0.32.0, HTTPX 0.28.1, Pydantic 2.14.1, pydantic-settings 2.16.1, python-jose 3.5.0, bcrypt 4.3.0, structlog 26.1.0.
- `.env` copied from `.env.example`, including `LLM_PROVIDER=mock`. No external GitHub or LLM requests were made. The issue gives no reporter OS/runtime to match, so these results apply to this recorded setup.
- Requests used HTTPX `ASGITransport` in one Python process: real authentication, API routes, background processing, and separate SQLAlchemy sessions against PostgreSQL. This does not test a browser, network server, or multiple worker processes. The transport waits for background tasks to finish; each POST is followed by GET `/reviews/{id}` to inspect stored results.

**Repeat the attempt**

1. Clone your fork, enter it, and check out the recorded commit. Follow `docs/SETUP.md`; I precreated a Python 3.12 venv to avoid using my system Python 3.14:

```sh
git clone https://github.com/malcolmxsc/pathreview-ai301-fa26-s1.git
cd pathreview-ai301-fa26-s1
git checkout f89c06fc3ff292df2a04a39ac51319d32a76b779
python3.12 -m venv .venv
cp .env.example .env
docker compose up -d
.venv/bin/pip install -e '.[dev]'
PATH="$PWD/.venv/bin:$PATH" make setup
```

`make setup` completed migrations and created the documented local seed accounts. Preserve the default mock provider. The package versions above record what the unpinned project requirements resolved to; pin those versions if your resolver chooses different ones. PostgreSQL must be healthy before the script runs; Chroma's unrelated startup failure is recorded above rather than counted as evidence for #33.

2. Save the script below as `repro_issue_33.py` in the checkout. It logs into the **local seeded** `user1@example.com` / `password1` account and creates a fresh profile with `github_username=issue33-local-fixture`. Each review uses that same returned profile id. No personal profile or private fixture is needed.
3. From that checkout, run `.venv/bin/python repro_issue_33.py`. The script first sends two sequential POST `/reviews` requests, then three pairs submitted with `asyncio.gather`, with no agent monkeypatch active. It compares stored status, sections, score, and error message, excluding unique ids and timestamps.
4. The last two experiments temporarily wrap `_run_agent_orchestration` in memory. The sequential control adds a 50 ms pause. The concurrent probe waits for two entries, with a 3-second timeout, before calling the original helper and preserving its output. This deliberately creates a scheduling window in the immediate-return placeholder. It edits no source file and restores the helper afterward. If same-profile processing were serialized, the first call would time out and maximum simultaneous entries would remain 1.

**Expected and observed**

Expected from the proposed serialization requirement: same-profile work does not enter the agent stage concurrently, even when that stage awaits.

Observed without instrumentation: all six concurrent reviews and both sequential controls completed with score 0.81 and three sections; their compared payloads matched. I saw no inconsistent output in these three concurrent trials.

Observed with instrumentation: the sequential control had maximum active count 1. The concurrent probe logged active count 2 for the same profile before either exit; both still completed with equal output. Relevant lines copied from the actual run:

```text
{"event": "baseline_sequential", "results_equal": true}
{"both_complete": true, "event": "baseline_concurrent", "match_sequential": true, "results_equal": true, "trial": 1}
{"both_complete": true, "event": "baseline_concurrent", "match_sequential": true, "results_equal": true, "trial": 2}
{"both_complete": true, "event": "baseline_concurrent", "match_sequential": true, "results_equal": true, "trial": 3}
{"both_complete": true, "event": "probe_summary", "instrumentation": "runtime agent wrapper; original agent output retained", "maximum_active_same_profile": 1, "mode": "controlled-sequential", "results_equal": true}
{"active_for_same_profile": 1, "event": "agent_enter", "label": "controlled-concurrent-A", "profile_id": "d5ce6993-3301-475b-8e6d-ddce6d44ba56", "seconds": 0.0088}
{"active_for_same_profile": 2, "event": "agent_enter", "label": "controlled-concurrent-B", "profile_id": "d5ce6993-3301-475b-8e6d-ddce6d44ba56", "seconds": 0.0102}
{"active_for_same_profile": 1, "event": "agent_exit", "label": "controlled-concurrent-B"}
{"active_for_same_profile": 0, "event": "agent_exit", "label": "controlled-concurrent-A"}
{"both_complete": true, "event": "probe_summary", "instrumentation": "runtime agent wrapper; original agent output retained", "maximum_active_same_profile": 2, "mode": "controlled-concurrent", "results_equal": true}
```

There was also a repeated application error during both baseline and controlled requests:

```text
github_ingestion_failed error="'raw_data' is an invalid keyword argument for IngestedSource" username=issue33-local-fixture
```

The service caught that error and continued to completion. This is an additional limit on the input path; I am not treating that error as the race condition.

**Conclusion and next step**

The controlled probe supports a narrow result: the current route/service path does not serialize two same-profile entries into the agent stage when that stage yields. It does not demonstrate naturally occurring stale reads, profile corruption, or inconsistent feedback. The current agent and RAG helpers return fixed placeholder output, so matching results do not establish that a future stateful implementation is safe. The ingestion error and unavailable vector store further limit this attempt. I will use this probe when investigating where a per-profile lock belongs, and will need a real stateful workload to verify the inconsistent-results part of #33.

I used AI assistance: Codex prepared and executed the setup/probe and helped write this report; Claude Code ran my installed `repro-check` skill on the drafts. The observations above come from the executed local run, with the instrumentation and limitations disclosed.

<details>
<summary>Complete runnable probe</summary>

```python
"""Run from the Path Review checkout; use only the local seeded database.

No application source files are edited. The final two experiments temporarily
wrap the real agent helper to measure overlap under a disclosed scheduling delay.
"""

import asyncio
import contextvars
import importlib.metadata
import json
import logging
import platform
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))

import httpx
import structlog

from api.main import app
from core.database import engine
from core.services import review_service

engine.echo = False
logging.basicConfig(level=logging.ERROR)
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
label = contextvars.ContextVar("request_label", default="unknown")


def emit(event, **facts):
    print(json.dumps({"event": event, **facts}, sort_keys=True), flush=True)


async def main():
    emit(
        "environment",
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        python=platform.python_version(),
        os=platform.platform(),
        versions={
            name: importlib.metadata.version(name)
            for name in ["fastapi", "starlette", "sqlalchemy", "asyncpg", "httpx"]
        },
        transport="in-process HTTPX ASGITransport; real auth, routes, background tasks, PostgreSQL",
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://pathreview.local"
    ) as client:
        response = await client.post(
            "/auth/login", data={"username": "user1@example.com", "password": "password1"}
        )
        response.raise_for_status()
        client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        response = await client.post("/profiles", data={"github_username": "issue33-local-fixture"})
        response.raise_for_status()
        profile_id = response.json()["id"]
        emit("fixture", profile_id=profile_id, source="fresh local profile owned by seeded user1")

        async def submit(name):
            token = label.set(name)
            try:
                created = await client.post("/reviews", json={"profile_id": profile_id})
                created.raise_for_status()
                review_id = created.json()["id"]
                fetched = await client.get("/reviews/" + review_id)
                fetched.raise_for_status()
                result = fetched.json()
                emit(
                    "review_result",
                    label=name,
                    review_id=review_id,
                    profile_id=result["profile_id"],
                    post_http=created.status_code,
                    status=result["status"],
                    score=result["overall_score"],
                    sections=len(result["sections"] or []),
                    error=result.get("error_message"),
                )
                return {k: result[k] for k in ["status", "sections", "overall_score", "error_message"]}
            finally:
                label.reset(token)

        # First exercise the existing code without wrapping any helper.
        sequential = [await submit("baseline-sequential-1"), await submit("baseline-sequential-2")]
        emit("baseline_sequential", results_equal=sequential[0] == sequential[1])
        for trial in range(1, 4):
            pair = await asyncio.gather(
                submit(f"baseline-concurrent-{trial}-A"), submit(f"baseline-concurrent-{trial}-B")
            )
            emit(
                "baseline_concurrent",
                trial=trial,
                both_complete=all(item["status"] == "complete" for item in pair),
                results_equal=pair[0] == pair[1],
                match_sequential=all(item == sequential[0] for item in pair),
            )

        original_agent = review_service._run_agent_orchestration

        async def probe(concurrent):
            active = 0
            maximum = 0
            entries = 0
            both_entered = asyncio.Event()
            start = time.monotonic()

            async def measured_agent(profile, ingestion_results):
                nonlocal active, maximum, entries
                active += 1
                entries += 1
                maximum = max(maximum, active)
                emit(
                    "agent_enter",
                    label=label.get(),
                    profile_id=str(profile.id),
                    active_for_same_profile=active,
                    seconds=round(time.monotonic() - start, 4),
                )
                if entries == 2:
                    both_entered.set()
                try:
                    if concurrent:
                        # Expose a scheduling window in the current immediate-return stub.
                        # With serialization, the first call times out and max active stays 1.
                        try:
                            await asyncio.wait_for(both_entered.wait(), timeout=3)
                        except TimeoutError:
                            emit("probe_wait_timeout", label=label.get())
                    else:
                        await asyncio.sleep(0.05)
                    return await original_agent(profile, ingestion_results)
                finally:
                    active -= 1
                    emit("agent_exit", label=label.get(), active_for_same_profile=active)

            mode = "controlled-concurrent" if concurrent else "controlled-sequential"
            with patch.object(review_service, "_run_agent_orchestration", measured_agent):
                if concurrent:
                    results = await asyncio.gather(submit(mode + "-A"), submit(mode + "-B"))
                else:
                    results = [await submit(mode + "-A"), await submit(mode + "-B")]
            emit(
                "probe_summary",
                mode=mode,
                maximum_active_same_profile=maximum,
                both_complete=all(item["status"] == "complete" for item in results),
                results_equal=results[0] == results[1],
                instrumentation="runtime agent wrapper; original agent output retained",
            )

        await probe(concurrent=False)
        await probe(concurrent=True)
        emit(
            "conclusion",
            baseline="three concurrent pairs compared with sequential requests",
            limitation="controlled overlap does not by itself demonstrate stale reads or inconsistent output",
            cleanup="local fixture retained for inspection; no external profiles or LLM calls used",
        )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

**Reproduction reflection**

My attempt separated overlapping work from inconsistent output. The controlled pause exposed two same-profile entries, but the current helpers returned fixed feedback, so I reported that I could not reproduce inconsistent results. The unrelated ingestion error and unavailable vector store further limit the test. A later investigation needs a stateful workload before claiming stale reads or corrupted feedback.

## Eval iterations

**Run history**

The runs below used the canonical installed files at `~/.claude/skills/repro-check/`, with `--skill`, `--rubric`, and `--evidence` pointing to that copy. The JSON results are included in `eval-details/`; revision snapshots are retained in the Unit 2 starter clone's `eval/iterations/` directory. The hand calibration of `calib-02` was a reject; it is not a scored harness run.

1. Full attempt, v1 (`run-01.json`): all 20 calls errored because Claude's OAuth session had expired. The harness printed `agreement: 0/0 scored items`. This is an authentication failure, not 0/20 rubric agreement; no submission transcript was saved. I restored sign-in before retrying.
2. First successful full run, v1 (`run-02.json`): `agreement: 18/20 scored items  (bar: 18/20: PASS)`. Categories: clear-accept 6/8, disclosure 1/1, no-evidence 4/4, unfollowable-comms 3/3, wrong-target 4/4. The disagreements were `pkg-03` and `pkg-05`, both rejected on Repository conventions.
3. Targeted v2 run, `--only pkg-03,pkg-05,pkg-20` (`run-03.json`): `agreement: 2/3 scored items`. I clarified follow-up comment requirements and distinguished AI assistance from a proven violation of human-authorship rules. `pkg-03` accepted; `pkg-20`, the disclosure canary, still rejected. `pkg-05` now passed conventions but failed Steps a stranger can run because the grader demanded the exact dependency list.
4. Targeted v3 run, `--only pkg-05,pkg-18,pkg-20` (`run-04.json`): `agreement: 3/3 scored items`. I clarified that an unambiguous fixture recipe can suffice when omitted values do not affect the trigger. `pkg-05` accepted; `pkg-18` still rejected on its private, unshared setup, and the disclosure canary still rejected. These partial runs did not establish the category floor or write a submission transcript.
5. Confirming full v3 run (`run-05.json`) with `--save-run eval-run.txt`: `agreement: 20/20 scored items  (bar: 18/20: PASS)`. Categories: clear-accept 8/8, disclosure 1/1, no-evidence 4/4, unfollowable-comms 3/3, wrong-target 4/4. The harness wrote the transcript, and I copied it to this directory without editing. This is the submitted run.

**Package analysis**

`pkg-20` (`ghostty-org/ghostty#13604`): my rubric decided **reject**, matching the gold label. Its environment, steps, and artifacts passed the proof checks. It failed Repository conventions because the sample comments omit the AI disclosure required by the captured policy. The harness recorded:

> AI_POLICY requires disclosure of tool and extent of AI use; neither the claim nor the repro report contains any AI disclosure

**Check rationale**

Quoting the pass condition of **Evidence addresses the issue**, exactly as it appears in the submitted `tools/repro-check/rubric.md`:

> At least one artifact shows what happened during the stated attempt and distinguishes the issue's behavior from an adjacent failure. For a claimed reproduction, the artifact demonstrates the reported symptom with its relevant trigger; merely showing that the program runs or that some error occurred is insufficient. For cannot-reproduce, artifacts show the attempted trigger and observed non-failure, with limitations stated.

I chose a comparison between the artifact and the issue rather than a requirement for a long report, a fixed number of steps, or an error screenshot. The operator swap in calibration `calib-03` illustrates the danger: a syntax error from changed HCL input is not the issue's runtime panic, regardless of how polished the explanation is. I kept this check unchanged during the eval revisions; the demonstrated ambiguity was in conventions and input completeness. Its cannot-reproduce clause keeps a useful negative result eligible without claiming the original issue is absent.

**Trade-offs**

Allowing equivalent diagnostics and concise fixture recipes reduces false rejections of useful follow-up comments, but it gives up a byte-for-byte record of every installed package and incidental message. That can miss a dependency-sensitive condition if I incorrectly judge an omitted value irrelevant. The allowance is limited to values that do not affect the trigger; missing trigger syntax, private configuration, and essential environment details still fail other checks.

I tested that boundary with `pkg-18`: after the steps clarification, the package with a private monorepo and unshared configuration still rejected. Because the conventions revision loosened a policy check, I also reran the single-item disclosure category, `pkg-20`, in both targeted runs; it rejected both times. These canaries support a narrow claim about the revisions, not a claim that every untested package stayed unchanged. The confirming full run checks the whole set.

---

Related paths: `eval-run.txt` in this directory; the installed skill's submission copy in `tools/repro-check/`.
