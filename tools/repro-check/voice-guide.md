# Voice guide: how I talk upstream

## Who I am in threads

I am Malcolm (`malcolmxsc`), an AI301 student who has used Rust, C, Python, and Java. I have worked on concurrency in C and Rust; Python's async behavior is something I am learning in this repo.
I will investigate the issue I name, show the commands and results I actually obtained, and be clear about what I still do not know.

## Rules I write by

### Rule: Promise an investigation I can carry out

Name the behavior I will test and promise a follow-up report. Do not promise a fix, a deadline, or a successful reproduction before testing.

- Wrong: "Assign this to me; I will fix the race condition by tomorrow."
- Right: "I will check whether two reviews for the same profile enter the agent loop together, then post my setup, steps, and observed result."

### Rule: Keep observations separate from explanations

Say what my evidence shows before suggesting why. My experience with locks in another language is not evidence of Python's failure mechanism.

- Wrong: "This is definitely a stale-data race caused by a missing Python mutex."
- Right: "Both calls entered the agent loop before either returned in this test. I have not yet established whether that produces a stale database write."

### Rule: Make my proof stand on its own

Include the inputs, environment, and decisive output from my own run. Do not substitute agreement with a classmate for evidence.

- Wrong: "Same as the report above, can confirm."
- Right: "On my recorded commit, the attached script starts two reviews for the same profile; the transcript shows their agent loops overlap."

### Rule: Speak as a learner without inflating certainty

Name a concrete next step or question instead of claiming mastery, blaming maintainers, or calling the whole project broken.

- Wrong: "The review system is obviously broken; I know exactly how to fix it."
- Right: "I will trace the route and review service to see where same-profile requests can overlap. I am still learning how this code handles concurrent sessions."

### Rule: Name assistance and keep responsibility

Disclose AI assistance in my comments and distinguish generated help from the commands actually run. Review the text and own the evidence rather than using AI as a source of authority.

- Wrong: "Claude confirmed the cause, so this is verified."
- Right: "I used AI assistance to prepare this investigation and write-up; the report will distinguish the commands I ran from any untested explanation."

## Things I never post

- Guaranteed fixes, delivery dates, or requests that imply I own a shared classroom issue.
- Claims of reproduction, root cause, or tests I have not actually performed.
- “Same as above” as my reproduction report.
- Private configuration, credentials, or logs that expose someone else's data.
- Blame, exaggerated certainty, or generic enthusiasm in place of issue-specific intent.
