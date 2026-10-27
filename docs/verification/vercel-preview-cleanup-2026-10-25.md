# Preview deployment cleanup — 2026-10-25

User authorized deleting all preview deployments except the three newest. Selection was by creation time across all preview states, including canceled records. Production deployments were excluded.

Vercel CLI reported 15 removals. A fresh complete deployment listing confirmed exactly three previews remain, none of the deleted IDs remain listed, and all 19 production records (18 ready, one canceled) remain. Storage savings have not been measured.

## Retained

- dpl_F37FU2hCiefgxvRyuuL2ppfKM4fb: READY, dev
- dpl_8UEbzNRyUVC1nqiuSZd2RKtkEP9Y: CANCELED, dev
- dpl_HvpytLeEYzw4VXMevyZzRWS4pLUy: READY, improve-evaluation-workflow-rag-quality

## Deleted

- dpl_6LxtvjxBkNsKoenKFsXUcfyK85vJ: codex/catalog-runtime-dependency
- dpl_23ihYjd7zX8HrURbEStMEwskeAfm: codex/product-image-release
- dpl_DbfoVSroyd5HA2YzLnnQ45P66Uc7: codex/evaluation-dashboard-and-print-inquiries
- dpl_6PaVeTxZnnuXiXxkg5ReMKqYbGZP: codex/evaluation-methodology-and-formulas
- dpl_BEArKeZxGwocdvfQKq4KPQFQzQYi: codex/evaluation-terminal-state
- dpl_ARGeW4sVQdLoWamWYfjwUFB8QMzC: codex/evaluation-worker-recovery
- dpl_8QMJQMv9uaKq46JRGzgvwx144kGU: codex/conversational-prompt-release
- dpl_2Vx1qgQR3zHjEPmoNp2nqyxQcqDD: codex/single-knowledge-base
- dpl_87GPshfNyRbWxD7HRKDb7umuELzo: codex/single-knowledge-base
- dpl_2USSa9aZLkv6uJYryzKLN4w4DVQa: codex/single-knowledge-base
- dpl_EjYboqM2XYkjitYWz9iw23Paw5kM: codex/whatsapp-reliability
- dpl_HBVjNFfvNSFn3ryHdXRqLQH81Egk: dev
- dpl_21Np92PPPhaVgztaKq7iraAizLbg: dev
- dpl_FPsxUCcwCPFdrPnpRv2vARdHXdib: dev
- dpl_GrRwhBE4MJZCJ7Engmop9wn4m6zH: dev
