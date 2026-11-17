# Candidate 9 Safeguard Test Results

## Result: SAFEGUARD_FAILURE

The requested broker-integrated controlled demo mode is **not implemented**.
The tests below exercise only an isolated, non-executing safeguard model;
they do not establish that actual order placement, position monitoring,
logging, reconciliation or shutdown are safe. Do not remove the kill switch,
arm an executor or place a trade on the basis of these tests.

## Executed tests

| Command | Result | Scope |
|---|---|---|
| `python -m unittest tests.test_candidate9_readiness_preflight tests.test_candidate9_risk tests.test_candidate9_validation_journal tests.test_candidate9_broker_observation tests.test_candidate9_reconciliation tests.test_candidate9_safeguard_model` | 28 passed | Synthetic snapshots, fake broker and temporary SQLite state; no real broker. |
| `python -m unittest discover -s tests` | 82 passed | Research, baseline and candidate-model regressions. |
| `python -m unittest discover -s paper_trading\tests` | 54 passed | Existing paper-trading mocks and tests. |

Model tests cover persistent completion/rejection/reconciliation latches;
kill-switch event and persistence; spread and gap boundaries; startup
position, pending order and synthetic health failures; synthetic 1R loss;
expiry; three modeled exceptions; the ten-count branch; and missing or
corrupt state. The ten-count branch is seeded directly in a test because
the one-trade latch otherwise stops this model after the first completion.
Additional fake-broker tests cover demo identity, permissions, positions,
pending orders, quote freshness and completed-weekend-bar signal derivation.
Pure reconciliation tests cover partial fills, weighted prices, signed
slippage, costs, internal identity and inconsistent evidence. They never
invoke MT5; the observer requires an already-connected module and does not
initialize a connection.

The new isolated journal tests verify persistent single intent, a permanent
completion/rejection latch, expiry, corrupt-state refusal and restart
handling of an unresolved intent. It is not integrated with broker actions,
and does not prove process-crash durability across an actual order call.
An expired intent now commits the expiry latch and raises an explicit
`VALIDATION_EXPIRED` error instead of returning like a successful attempt.
Pure risk tests validate long and short fixed levels, tick and volume grids,
close-side broker stop distances and a caller-supplied account-currency risk
budget. The estimate and broker inputs are not independently validated.

The read-only preflight combines the signal, fake-broker observation, model,
journal and risk checks. Tests cover a passing **non-executing** path, kill
switch persistence, unexpected positions, the exact 3-pip spread boundary,
daily loss, risk failure, a missed entry, unverified timestamps and broker
exceptions. These are not end-to-end order or reconciliation tests.

Six additional fake-broker position-watch tests cover protection changes,
unexpected position identity, stale quotes, the 1R loss boundary, a kill
switch and closure requiring reconciliation. The watcher is invoked only by
tests; no service or broker polling loop is running. It cannot cancel or
close exposure, and its daily P&L is caller-supplied.

The read-only derivation also matched the existing candidate generator's
27 historical signals in 2025 and 31 in 2026 using the corresponding
completed historical bars. This does not verify broker timestamp semantics
or the selection of bars from an MT5 feed.

## Not validated

- Real broker account identity, connection, permissions, quote freshness,
  position and pending-order queries, and race-free pre-submission checks.
- Candidate signal timing using MT5 weekend history and broker timestamp
  semantics, stale Friday data, and handling of missing observations.
- Any real order lifecycle, rejection, partial fill, attached stop/target,
  slippage, concurrent positions, restart recovery, or broker history.
- Calculation of actual daily 1R loss, currency conversion, floating P&L,
  commissions or broker-side realized P&L.
- Complete candidate-specific trade log, reconciliation to MT5, isolated
  metrics, ten-trade automatic report, and fail-closed integration.
- Immediate kill-switch enforcement while a position is active or an order
  request is in flight. A file alone cannot enforce a broker shutdown.

No live or demo order was submitted, no strategy was armed, and no broker
connection was attempted for this task.
