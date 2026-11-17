# Observer Latency Investigation

## Conclusion

**LATENCY_BLOCKING**

The reported **205.2 seconds** is not evidence that each observer request
takes 205 seconds. It came from a one-poll acceptance run whose only sample
was taken 205.2 seconds after the signal bar's expected close. A continuously
running five-second poll loop detects a newly available completed bar within
approximately one polling interval plus feed/processing time, assuming MT5
publishes that completed bar promptly.

That is still not sufficient to satisfy frozen V1's exact entry rule. V1
requires entry at the **next M5 bar open**. The completed signal bar becomes
available at that boundary, and a poll-and-evaluate cycle can only report it
at or after availability. The tested five-second loop cannot guarantee a
zero-delay detection, and the required human review and manual entry add
unmeasured time. Detection within the following five-minute candle is not the
same as execution at its open.

## How observation time is measured

`signal_observer.observe_latest_bar()` first reads and validates the recent
completed bars, evaluates the latest signal, checks for a duplicate, and then
calls `_broker_now()` immediately before constructing and appending the
observation row. Therefore the stored observation timestamp is approximately
the end of the feed/evaluation work. It does not record poll-start time,
MT5 request-start time, MT5 response time separately, or when the terminal
first made the completed bar available.

The report's timing anomaly compares that observation time with the signal
bar label plus five minutes. It is diagnostic; it does not prevent the row
from being written or enforce trade eligibility.

## Continuous versus one-poll behavior

`observe()` runs an unbounded loop by default. After each poll it sleeps for
`poll_interval_seconds`, which defaults to **5 seconds**, then polls again.
`--max-polls` is optional and exists for bounded runs/tests. The post-migration
acceptance invoked the observer with `max_polls=1`, so it performed exactly
one query and stopped; there were no earlier or subsequent polls in that
acceptance run.

Consequently, the exact process-start delay before that one query was not
measured. The recorded 205.2 seconds is the age of the sampled signal bar at
that query, consistent with the test being invoked late, but the available
trace cannot distinguish late process startup from a delayed one-shot
invocation.

## Controlled continuous-poll simulation

The actual observer loop was run with its MT5 feed, clock, and sleep
deterministically simulated. The feed exposed a completed LONG signal bar
immediately at the expected close; the observer used the normal five-second
poll interval, timestamped and appended the observation, and generated its
report. The scenarios were:

| Scenario | Delay from signal close to detection | Within following 5-minute bar |
|---|---:|---|
| Poll began 4.9 seconds before close | 0.1 seconds | Yes |
| Poll began 0.1 seconds after close | 0.1 seconds | Yes |
| Single poll began 205.2 seconds after close | 205.2 seconds | Yes |

These are controlled simulations, not a live MT5 bar-boundary measurement.
The 205.2-second value is below the 300-second duration of an M5 bar, but it
is 205.2 seconds after that bar opened and therefore cannot be treated as an
entry at its open.

## Feed retrieval measurement

Three consecutive read-only MT5 completed-bar retrievals were timed. Each
`get_recent_m5_bars(count=21)` call took **0.0003–0.0004 seconds** locally.
The returned latest bar did not change during this short sample; its age
advanced from 89.0 to 93.1 seconds. Thus this measurement establishes that
the API call was fast for those three requests, but does **not** measure
terminal publication delay at a new M5 boundary.

No evidence from the current sample attributes the 205.2 seconds to MT5
request latency or timestamp arithmetic. It was measured after the feed
request and signal evaluation, and the call duration sample was far shorter.

## Cause assessment

| Candidate cause | Finding |
|---|---|
| Late process/test start | **Most consistent explanation for 205.2 seconds.** The acceptance was explicitly one poll, executed at that age. Exact startup delay was not separately logged. |
| Polling configuration | Default continuous interval is 5 seconds. This can add up to roughly one interval to detection, plus request/evaluation time; it does not explain a 205-second wait in a continuously active process. |
| MT5 feed latency | Three feed calls were sub-millisecond, but no bar transition was observed. Boundary publication latency remains unmeasured. |
| Timestamp calculation | The observation clock is sampled after retrieval/evaluation; no evidence indicates that timestamp arithmetic added 205 seconds. |
| Architectural limitation | **Present for the exact V1 entry point.** A completed-bar signal is only available at the next-bar boundary; polling reports it after it becomes available, and manual review/entry latency is not bounded or measured. |

## Validation

- `python -m unittest paper_trading.tests.test_signal_observer paper_trading.tests.test_live_signal_engine`
  — **12 tests passed**.
- The controlled simulation exercised multiple polls and verified the row was
  logged once with the expected signal and timing.
- Live MT5 API retrieval was sampled three times in read-only mode; the sample
  did not span a completed-bar transition.

## Disposition

The specific 205.2-second observation is an artifact of a one-shot poll being
run late, not evidence of a 205-second continuous-poll limitation. A
continuously running observer should ordinarily detect the bar within the
following M5 candle when feed publication is prompt. But V1 specifies an
entry at that candle's open, and the observer plus human-in-the-loop process
cannot guarantee that exact opening entry. No strategy rule or polling
configuration was changed in this investigation.

LATENCY_BLOCKING
