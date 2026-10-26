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
