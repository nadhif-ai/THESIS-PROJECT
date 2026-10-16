# Asia Visual Grafika chatbot workspace

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Administrators of the printing business manage customer guidance, inspect chatbot answers, and monitor WhatsApp and evaluations. Customers use WhatsApp, rather than this workspace. This reading was confirmed in the dashboard design discussion on 14 October 2026.

## Product Purpose

Keep the published printing knowledge accurate and make failures in retrieval, answer quality, or message delivery visible and actionable.

## Operating Context

Administrators prepare a draft, upload or edit documents, configure passages, index, test in the playground, and publish a ready version. WhatsApp, playground, and evaluations use the same answer pipeline. Evaluation references require a human review. Answering and judge models are configured independently.

## Capabilities and Constraints

- Existing React/Vite frontend, shadcn/Radix controls, FastAPI backend, and SQLite administration state.
- One local background worker runs indexing, evaluation, generation, and reporting jobs.
- WAHA receives customer messages through an authenticated webhook and a persistent inbox worker.
- API configuration is not proof of a live connection. Published knowledge is not proof that WhatsApp is reachable.
- Evaluations use model APIs; UI verification must use offline test doubles for paid operations.
- Ordering and payment remain with the shop administrator.

## Brand Commitments

The user selected paper + ink: light surfaces, decisive typography, and the existing blue accent. The supplied sidebar reference requires a persistent compact desktop icon rail when collapsed.

## Evidence on Hand

README.md, the administration API, persisted versions/conversations/jobs, baseline results, reviewed dataset files, and the WAHA inbox. Counts and statuses must come from these sources. An unavailable value must remain unavailable.

## Product Principles

- Show the work an administrator needs to do next.
- Keep draft preparation distinct from customer publication.
- Separate quality failures, provider failures, and reporting failures.
- Show observed progress and check times, without invented estimates.
