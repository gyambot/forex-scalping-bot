# Next Step Recommendation

## Status

The project now uses the explicit-offset broker-time contract in
[BROKER_TIME_CONTRACT.md](./BROKER_TIME_CONTRACT.md). Configure
`MT5_BROKER_UTC_OFFSET` to match the server clock displayed by the connected
terminal (`+02:00` or `+03:00` as applicable) before relying on live quote or
bar timestamps. The migration did not perform a live terminal recheck.

The MT5 connector remains read-only. A successful healthcheck validates
connectivity and account identity; it does not prove market-open status,
timestamp semantics, next-bar execution readiness, or authorize demo orders.

## Recommended next action

1. Confirm the demo account/server and compare the configured offset with the
   terminal's displayed broker clock.
2. Run the read-only healthcheck and signal observer; investigate any clock,
   quote-freshness, duplicate-bar, or sequencing anomaly before relying on the
   observations.
3. Keep the terminal and connector read-only during this verification. Do not
   enable trade permissions, submit orders, or change V1 as part of this check.
4. Follow the separate demo execution checklist before any human-operated
   demo activity. The timestamp migration by itself is not execution approval.
