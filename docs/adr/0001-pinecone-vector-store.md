---
status: accepted
date: 2026-10-12
---

# Adopt Pinecone for chatbot vector storage

The project serves one business and supports both thesis evaluation and real WhatsApp conversations. We will capture the existing Chroma retrieval baseline, then migrate ingestion and retrieval to Pinecone to use managed vector storage as the application develops into an administered service.

Continuing with local Chroma would keep the system self-contained; Pinecone introduces an external service, credentials, network dependence, and usage costs in exchange for managed vector persistence. This choice alone does not establish better answer quality: comparisons must report retrieval and answer quality separately from the storage migration.

The user selected the immediate work order as baseline capture, Pinecone migration, then a shadcn admin dashboard with a playground and DeepEval integration. The first comparison preserves the existing E5 model, normalization and prefixes, chunking, prompts, and retrieval settings. The existing `chatbot-avg` index has been verified as ready with dimension 384 and cosine similarity. Knowledge publication will use draft versions followed by an explicit publish action. Application implementation awaits review of the written design.
