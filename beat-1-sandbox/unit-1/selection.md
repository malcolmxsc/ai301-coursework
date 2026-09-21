# Unit 1 — Issue Selection

Path: `beat-1-sandbox/unit-1/selection.md`

---

## Selected issue

**Issue link**

https://github.com/codepath/pathreview-ai301-fa26-s1/issues/33

**Verdict output**

```
Candidate: https://github.com/codepath/pathreview-ai301-fa26-s1/issues/33
"Concurrent review requests for the same profile can produce inconsistent results"

Repository is not archived      pass   gh repo view: archived: false
Maintainer liveness             pass   step 1 found no maintainer reply across 5 recently
                                       updated issues (#69-#73); step 2 fallback: 3
                                       default-branch commits on 2026-09-16, within 30 days
Newcomer-friendly scope         pass   maintainer-filed; states the outcome ("Add a
                                       per-profile lock to serialize concurrent reviews")
                                       and names api/routes/reviews.py and
                                       core/services/review_service.py; no competing proposals
No active contributor           pass   assignees: none; no linked or referencing PRs; 0 comments
Contribution policy allows      pass   no CONTRIBUTING.md at root or in .github/, no AI policy
  the work                             file; silence passes
Repository activity (preferred) pass   last push 2026-09-16
Good first issue signal         fail   labels: enhancement, api, tier-3 — no beginner label
  (preferred)

Accepted. Ranked first of four accepted candidates on the fit profile: concurrency
and locking are the closest work in this repo to low-level systems. The preferred
good-first-issue signal fails here and passes on #61, but preferred checks do not
change a verdict and fit ordered the accepted list.

```json
{
  "item": "https://github.com/codepath/pathreview-ai301-fa26-s1/issues/33",
  "checks": [
    {"name": "Repository is not archived", "grade": "pass",
     "evidence": "gh repo view: archived: false"},
    {"name": "Maintainer liveness", "grade": "pass",
     "evidence": "Step 1 found no maintainer reply across 5 recently updated issues; step 2 fallback: 3 default-branch commits on 2026-09-16, within 30 days"},
    {"name": "Newcomer-friendly scope", "grade": "pass",
     "evidence": "Maintainer-filed, states the outcome ('Add a per-profile lock to serialize concurrent reviews') and names api/routes/reviews.py and core/services/review_service.py; no competing proposals"},
    {"name": "No active contributor", "grade": "pass",
     "evidence": "assignees: none; no linked or referencing PRs; 0 comments"},
    {"name": "Contribution policy allows the work", "grade": "pass",
     "evidence": "No CONTRIBUTING.md at root or .github/, no AI policy file — silence passes"},
    {"name": "Repository activity", "grade": "pass",
     "evidence": "Last push 2026-09-16"},
    {"name": "Good first issue signal", "grade": "fail",
     "evidence": "labels: enhancement, api, tier-3 — no beginner label"}
  ],
  "verdict": "accept"
}
```
```

---

## Eval iterations

**Run history**

Six runs, in order:

1. Full run — `agreement: 14/20 scored items  (bar: 18/20: below the bar)`
2. Targeted `--only` run, 7 items — `agreement: 5/7 scored items`
3. Full run — `agreement: 15/20 scored items  (bar: 18/20: below the bar)`
4. Targeted `--only` run, 9 items — `agreement: 9/9 scored items`
5. Targeted `--only` run, 5 items — `agreement: 4/5 scored items`
6. Full run — `agreement: 19/20 scored items  (bar: 18/20: PASS)`

The last score matches the agreement line in the committed `eval-run.txt`.

**Issue analysis**

`issue-12` (bookwyrm-social/bookwyrm#1133). My rubric's decision: **reject**.
Gold label: **reject**.

The gold note reads: "passes every liveness, scope, and claim check; the repo's
contributing docs ban AI-generated code and documentation outright." My rubric
reached the same verdict on exactly one check. Its recorded evidence for the
run in `eval-run.txt` was:

> "CONTRIBUTING.md: 'We do not accept AI-generated code or documentation.'"

which quotes the bundle's repo-facts line:

> contribution policy (CONTRIBUTING.md -> docs.joinbookwyrm.com/contributing.html,
> section "Generative AI"): "Meaningful human interaction is the whole point of
> BookWyrm. We do not accept AI-generated code or documentation. If you are unsure
> how something in BookWyrm works, please ask for help – we are keen to help other
> humans to understand and contribute to the project."

Every other check passed: maintainer liveness ("Sample includes maintainer
responses at 0.3 and 0.5 days"), scope ("Bounded single UI feature; maintainer
already specified the implementation approach"), and no active contributor
("jrings's 2024-09-19 attempt predates the 2026-08-12 capture date by far more
than 30 days with no subsequent activity, so it is stale").

Worth recording: on my first rubric, `issue-12` also came out `reject` and was
counted as agreement, but for the wrong reasons — it failed maintainer activity
and the claim check, and the rubric had no policy check at all. Both of those
failures disappeared when I fixed those checks for other issues, so the
agreement on this item was coincidental until the policy check existed to carry
it.

**Check rationale**

Quoting `No active contributor` as currently written in the uploaded
`rubric.md`:

> Pass if nobody is currently assigned to the issue, no linked or referenced
> pull request is open, and no unexpired claim comment stands. Fail if an
> assignee is set, or if any linked or referenced pull request is open: an open
> PR is live work on the issue no matter how long it has sat idle, and the
> staleness exception below never applies to one. Closed or merged pull
> requests are not claims. The staleness exception applies to claim comments
> only: a comment claiming the issue that is more than 30 days old at the
> bundle's capture date, with no subsequent activity from that contributor and
> no open PR of theirs, counts as stale and does not fail this check.

The staleness exception exists for `issue-09`, whose gold note reads "the 2022
claim is stale and the maintainer invited takers" — a four-year-old comment
should not block anyone. But an earlier version applied that exception to any
claim, and the grader used it on `issue-18`'s open pull request, writing:

> "only submitted PR (#9685, opened 2025-06-21 by diljitsgit) has had no
> subsequent activity for >30 days, meeting the rubric's stale-claim exception"

That accepted an issue whose gold note is "no assignee, but open linked PRs and
a stack of claim comments." The current wording splits the two kinds of
evidence: an open PR is always a live claim, and only comments can expire.

**Trade-offs**

What this check gives up: it will reject an issue whose open PR is genuinely
abandoned. An open PR from two years ago that nobody will ever finish still
fails the check, and the newcomer who could have picked the work up is turned
away. I accepted that cost deliberately — reading an open PR as abandoned is a
judgment a newcomer is not well placed to make, and being wrong means duplicating
someone's in-flight work.

The change did move a result. `issue-18` went from `accept` (disagreeing with
gold) to `reject` (agreeing) once open PRs stopped expiring. I re-ran the whole
claimed category with `--only issue-18,issue-09,issue-03,issue-08,issue-13` as
a canary, because `issue-03`, `issue-08`, and `issue-13` all carry open PRs and
were already agreeing. That run returned `agreement: 4/5 scored items`: all four
open-PR issues rejected correctly, and the one disagreement was `issue-09`,
which failed a different check (`failed: Maintainer liveness`) while its claim
check passed on the intended evidence:

> "Assignees: none; linked PR #11627 is closed; sole claim comment from
> MesaJonathan (2022-01-20) is over 4 years stale with no follow-up or open PR."

So the exception still fires where it was designed to, and the open-PR rule did
not cost anything elsewhere.

---

## Selection rationale



**1. Fit to my interests and the time available.**

The issue is a race condition: two review requests for the same profile can enter
the agent loop at once, and the second can read state the first already changed.
The fix is a per-profile lock across 'api/routes/reviews.py' and
'core/services/review_service.py'. Concurrency and locking are the closest thing
in this repo to the low-level systems work I want to get better at. I had Claude
analyze the subject material for all the other issues on the repo, and this one
was the closest fit to my interest — more so than the other candidates I graded
(#70, an indented parser test fixture; #65, misconfigured async mocks; #61, a
one-line 'sqlalchemy.text()' wrap in a health route). It is also the largest:
'tier-3', estimated 6–9 hours, against 2–4 for the others.

**2. What the verdict identified correctly, and what I weighed that the rubric
could not.**

The verdict was right that nothing blocks the issue: no assignee, no linked PRs,
no comments, an unarchived repo with commits four days old, and no contribution
policy to violate. It was also right that the scope is decided — the maintainer
names the mechanism rather than asking for a discussion.

What it could not see is difficulty. My rubric has no difficulty check, so it
rated this 'tier-3' concurrency bug exactly as acceptable as #61's one-line fix.
"Decided" and "appropriately sized for a first contribution" are different
properties, and my scope check only tests the first.

**3. Anticipated difficulty in claiming it.**

The most difficult thing in claiming it could be unknown territory and navigating the inner workings of python race conditions, most of my work fixing race conditions have been in c and rust so it will be different dealing with python that's the biggest challenge I see.

---

Related paths: `eval-run.txt` in this directory; skill files in `tools/issue-select/`.
