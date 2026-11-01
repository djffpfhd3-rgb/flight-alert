# flight-alert

Status: diagnostic only. Scheduled monitoring and production notifications are not enabled.

The original Telegram test workflow is preserved. The new verification workflow is manual-only. An UNKNOWN result fails the job instead of reporting success. A successful unit test run is not proof of live availability access.

Files:
- trinity_check.py: conservative booking-page verification; no security-screen or queue bypass.
- alert_state.py: notification transition logic. UNKNOWN preserves the last confirmed state, SOLD_OUT rearms notifications, and failed delivery remains retryable.
- test_trinity.py and test_alert_state.py: eight unit tests.

Run tests with `python -m unittest -v`.

Persistent operational state and production Telegram delivery are not connected. Enable scheduling only after live retrieval is validated in the intended runtime.
