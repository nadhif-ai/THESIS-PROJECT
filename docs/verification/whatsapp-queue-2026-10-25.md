# WhatsApp queue investigation, 25 October 2026

## Findings

- Production deployment `dpl_9nbp3JPRLgVbfcuDushS8neNjXEX` ran commit `a51ec95`.
- Message fingerprint `aab95e742e1d` was received at 06:47:54 UTC. Its execution lease began at approximately 06:47:56 UTC.
- A callback at 06:48:01 UTC raised `RuntimeError("Inbox item is pending; retry queue delivery.")` while the inbox item was still being processed. This exception requests redelivery; it does not establish a disconnected WhatsApp session.
- The item reached terminal status `uncertain` at 06:48:07 UTC with a text delivery checkpoint and no provider reply ID. A read-only WAHA history check found the incoming message but no matching outgoing answer.
- The existing send exception handler discarded the exception class, and `process()` logged `phase=sent` even when `send_reply()` recorded an uncertain outcome. The exact historical transport failure cannot be recovered from that evidence.
- WAHA reported `WORKING`, with its GOWS client and stream ready. The database contained no queued, generating, or sending items when first inspected.
- A fresh user-sent message, fingerprint `fff590fedc8d`, received at 07:08:14 UTC, completed with one text reply and delivery ACK `2` before deployment of the patch. This confirms recovery of the live delivery path; it does not establish why the earlier transport failed.

## Changes

- Request expected redelivery using the installed Vercel Queue SDK's `RetryAfter(10)` directive rather than a generic runtime error.
- Log the message fingerprint and pending status when deferring a callback.
- Enable phase logging in the standalone subscriber, which does not import the FastAPI logging setup.
- Preserve and log only the transport exception class for uncertain delivery; never log the raw exception, request credentials, or customer message.
- Replace the unconditional `phase=sent` message with `phase=delivery_completed`. The consumer's final log records the persisted outcome.
- Preserve ordering, execution leases, idempotency, and the prohibition on automatic replay of uncertain sends.

## Verification

The existing out-of-order callback test failed with the reported RuntimeError before the retry change and passed afterward. A new transport failure test reproduced the missing diagnostic and false sent log before the logging change, then passed afterward. It also checks that a duplicate callback does not resend an uncertain message and that raw exception content is absent from logs.

Focused verification: 25 tests passed across queue, transport, and typing tests using disposable PostgreSQL on loopback port 54585. No test connected to production. Production database and WAHA history inspection was read-only; the earlier uncertain message was not resent.

Full offline suite: 327 passed, 11 skipped, two dependency deprecation warnings. `git diff --check` passed. The production frontend TypeScript/Vite build passed during deployment.

## Production verification

The patch was deployed from the local working tree using the Vercel CLI to `dpl_HnyVMwa7Mx7nVpvymd7uW9iujToc`, now serving `https://chatbotta-nadhif.vercel.app`. The deployment is READY and `/health` returned HTTP 200 with status `ready`. Source changes remain uncommitted; the deployment's inherited Git metadata identifies the base commit, not the patch.

Three fresh user messages completed on this deployment:

| Message fingerprint | Received (UTC) | Final status | Reply count | Delivery ACK |
| --- | --- | --- | --- | --- |
| `8266d3e32ca4` | 07:12:32 | sent | 1 | 2 |
| `56fe9c0df9db` | 07:12:43 | sent | 1 | 2 |
| `c3911889fd06` | 07:12:49 | sent | 1 | 2 |

Production logs confirm receipt, claim, generation, sending, delivery completion, and persisted final status for all three. These messages did not overlap in execution, so retry contention was verified by the offline out-of-order test, including propagation through the asynchronous subscriber and AnyIO worker thread. Live verification confirms the patched deployment's successful end-to-end delivery.
