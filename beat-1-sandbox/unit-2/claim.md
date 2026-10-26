I am investigating #33, where two review requests for the same profile may enter the agent loop together and read stale profile state. I will trace `api/routes/reviews.py` and `core/services/review_service.py`, then try concurrent same-profile requests and compare their execution with sequential requests. I will post a reproduction report with the tested commit, environment, runnable steps, and observed output, including any limits if I cannot reproduce the behavior.

I used AI assistance to prepare this investigation and write-up.
