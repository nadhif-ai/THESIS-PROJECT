## Problem Statement

Customers currently receive catalog illustrations automatically when discussing a new product, even if they only ask about printing, materials or prices. In the reported conversation, asking to see a standing banner was not recognized correctly, and a later reply said the preview was unavailable while displaying the image underneath. This makes the chatbot's capabilities and product examples confusing.

Customers need to request illustrations naturally, request other products or previous images again, and receive an image followed by relevant price/product details. Playground and WhatsApp must follow the same conversational policy and presentation order.

## Solution

Show a catalog image only in response to a customer image request. Resolve the requested product and visual coverage using the current conversation and approved catalog, then coordinate the answer with the actual attachment decision.

For a suitable image, show one illustration first and a separate text message underneath containing concise, relevant prices and product details from the published knowledge version. The customer need not ask for price again. Permit successive requests for different products and explicit repeats. If the request is ambiguous or the requested visual is unavailable, explain the limitation or ask for clarification without attaching a misleading substitute.

## User Stories

1. As a customer, I want to discuss a product without receiving an unsolicited image, so that the conversation stays focused.
2. As a customer, I want price questions to receive text unless I request a visual, so that unnecessary media does not interrupt my inquiry.
3. As a customer, I want material and variant questions to avoid automatic attachments, so that images appear only when useful to me.
4. As a customer, I want a textual product comparison without an automatic picture, so that I control when media is sent.
5. As a customer, I want to request a visual comparison explicitly, so that I can see relevant differences.
6. As a customer, I want wording such as “gambarnya,” “fotonya,” and “preview” to be understood, so that I can speak naturally.
7. As a customer, I want contextual wording such as “mau liat yang banner x tegak” to identify a visual request, so that I do not need a rigid command.
8. As a customer, I want “banner x” and “banner y” to resolve to the correct standing products, so that a generic banner does not replace my intended product.
9. As a customer, I want an implicit follow-up to use the clearly established product, so that I do not have to repeat its name.
10. As a customer, I want a clear product change to override earlier context, so that the next image matches my new request.
11. As a customer, I want to see the requested illustration before its explanatory message, so that I can associate the details with the product shown.
12. As a customer, I want concise price details beneath the image, so that I do not need a separate price question.
13. As a customer, I want applicable material or size options explained when needed, so that I understand why prices differ.
14. As a customer, I want the chatbot to ask for missing specifications when no exact quote is supported, so that it does not invent a price.
15. As a customer, I want to request another product's image in the next turn, so that I can explore the catalog interactively.
16. As a customer, I want to request the same illustration again, so that an earlier image request does not block a new explicit request.
17. As a customer, I want at most one image per reply, so that a request does not produce excessive media.
18. As a customer, I want a suitable single comparison image or a clarification when requesting several products, so that the chatbot does not pick an arbitrary product.
19. As a customer, I want “no image” or text-only instructions respected, so that the chatbot follows my current preference.
20. As a customer, I want a shipping question containing “kirim” to remain a shipping question, so that it does not trigger an image or bypass repetition controls.
21. As a customer, I want an honest explanation when no appropriate image exists, so that the text and attachments agree.
22. As a customer, I want unpictured variants to be identified accurately, so that a representative illustration is not mistaken for exact physical stock.
23. As a customer, I want ambiguous requests such as an unspecified sticker product clarified, so that I receive the correct illustration.
24. As a customer, I want available price/details text even if the image fails, so that the conversation remains useful.
25. As a customer, I want a brief notice when an explicitly requested image definitively fails, so that I understand why it did not appear.
26. As a customer, I want interrupted or uncertain sends to avoid automatic duplicate media, so that technical retries do not spam the conversation.
27. As an administrator, I want Playground to use the same image policy and image-before-details presentation as WhatsApp, so that previews represent customer behavior.
28. As an administrator, I want accurate decision reasons for requested images and suppressed attachments, so that I can diagnose matching issues.
29. As an administrator, I want preview repetition history separated from customer delivery state, so that testing does not affect customer allowances.
30. As an administrator, I want existing approval, enable/disable and catalog management controls preserved, so that only eligible illustrations are used.
31. As an operator, I want the selected image, answer and product focus checkpointed consistently, so that recovery does not silently change the response.
32. As an operator, I want readiness and delivery evidence distinguished, so that an enabled catalog or healthy WAHA session is not reported as a deployed, verified customer feature.

## Implementation Decisions

- Replace automatic new-product/comparison attachment triggers with a customer-image-request gate. Product focus may still advance during normal discussion, without triggering media.
- Use the existing shared RAG conversation pipeline for WhatsApp and Playground. Do not introduce channel-specific retrieval or answer generation.
- Improve the shared selector's Indonesian visual-request recognition, including suffixes, preview wording, contextual view requests, negation and text-only instructions. Mere shipping verbs must not count as visual intent.
- Extend canonical product aliases to handle reversed standing-banner names. Explicit current-turn products take precedence over earlier focus; implicit requests inherit only an unambiguous product.
- Preserve the distinction between source-only variants and visibly depicted variants. Select only enabled, approved assets with appropriate product and visual coverage; otherwise omit the image and clarify or explain.
- A new explicit request can reuse an asset already shown, regardless of earlier automatic-suppression state. It is a new customer action, not authorization to replay an old uncertain delivery job.
- Keep the one-image-per-reply limit. A multi-product request uses one suitable comparison asset or asks which product to show first.
- Make the attachment decision before invoking the answering model. Supply a narrow, trusted availability state and product label, sufficient to coordinate the text with the selected illustration or actual limitation.
- Keep catalog descriptions and image metadata outside the factual price/specification context. Prices and authoritative details continue to come from the published knowledge version; never infer prices or measurements from image appearance.
- For a matched image request, generate a concise price/detail message without requiring another customer question. Explain relevant options or ask for missing specifications instead of inventing an exact quote.
- Change presentation and WAHA delivery order to image first, then a separate price/detail text message. Keep the image caption short and descriptive; do not duplicate the full price explanation in it.
- Do not claim an external preview URL is unavailable while attaching a selected catalog illustration. Do not claim delivery before its outcome is known. Missing or disabled image coverage must produce an accurate explanation and no unrelated substitute.
- Apply request-only gating to legacy knowledge-media fallback as well as catalog selection, so fallback cannot restore unsolicited attachments.
- Atomically persist the generated text, pinned asset identity/revision/object reference, decision reason and product focus under the existing inbox lease before external delivery. Suppress the image if answer generation fails.
- Preserve independent image, text and failure-notice checkpoints, provider identities, receipt correlation, execution leases, bot-enabled fences and conservative uncertain-send recovery. Changing ordering must not weaken these invariants.
- An image failure or uncertain image outcome must not erase or block the available detail text. Do not automatically replay an image whose outcome is uncertain; a definitive failure on an explicit request receives the existing brief failure notice. Record text/notice outcomes independently too.
- Keep Playground preview state isolated from customer delivery state. Render the same selected illustration before its detail text and expose meaningful requested/suppressed decision reasons; new-product detection alone is no longer a media trigger.
- Retain existing catalog registry, dashboard Save semantics, public catalog Storage, private staging/originals, and all 27 approved illustrations. No schema or public API expansion is required by this specification; preserve existing interfaces unless a demonstrated implementation need requires a compatible extension.
- Keep the current embedding identity, Pinecone index and published-knowledge activation procedure unchanged.

## Testing Decisions

- Carry forward the already approved conversation and delivery testing boundaries; no additional interview or newly proposed seam is needed. Prefer the highest existing observable boundary: the shared conversation result, exercised through the authenticated Playground API, with WAHA's existing transport boundary verifying external send order and recovery. Do not add test-only public endpoints.
- Good tests assert externally observable answers, selected asset or no asset, presentation/send order, and recovery outcomes. They must not depend on private helper structure or repeat the implementation's selection calculations.
- Use existing conversation routing, shared-RAG/catalog, authenticated Playground and WAHA delivery/queue regression patterns as prior art. Use deterministic provider fakes for offline checks and disposable loopback PostgreSQL for persistence; never point automated tests at hosted PostgreSQL.
- Reproduce the exact reported three-turn conversation: an initial banner inquiry receives no image; the contextual standing-banner view request resolves X-banner; the later explicit X-banner preview request attaches its illustration and consistent detail text, never an unavailable-preview denial.
- Cover ordinary product, price, material and textual comparison questions without images; visual comparisons with a suitable comparison image; suffix/slang/preview recognition; shipping wording; explicit negation; and contextual visual follow-ups.
- Cover requests for product A, product B, then A again, as well as an immediate explicit same-image repeat. Every requested reply remains limited to one image.
- Cover ambiguous products, disabled assets, unsupported and source-only variants, and multi-product requests without a suitable comparison. Assert clarification or an accurate limitation rather than a misleading attachment.
- Verify price/details text is grounded in supplied active-knowledge evidence, distinguishes material/size options, and avoids a fabricated exact quote when required specifications are absent.
- Verify image-before-details ordering in Playground and actual WAHA transport calls. Test image rejection, image timeout/missing identity, image accepted followed by text failure/uncertainty, queue redelivery, expired leases, disable fences and recovery without duplicate known or uncertain parts.
- Verify selected asset and focus remain coordinated with the persisted answer across generation retries and catalog edits; retain provider receipt correlation and preview/customer state isolation.
- Run focused regressions during implementation, the full offline backend suite, existing JavaScript regression checks, and frontend lint/typecheck/build. Inspect desktop/mobile rendering and accessibility of the changed message presentation.
- After deployment is separately authorized, use a controlled test account or the WAHA account's own identity for a fresh customer-channel verification. Record provider IDs and actual ACK levels; provider acceptance alone must not be described as delivered/read confirmation. Paid evaluation runs are not required by this specification.

## Out of Scope

- Several separate images in one reply, albums, carousels or unsolicited catalog messages.
- Recognition or retrieval from photographs uploaded by customers.
- New image generation, replacement of the approved asset set or re-reviewing the settled seven product groups.
- Multimodal embedding migration, reindexing Pinecone, adding a new vector store or mixing illustrative metadata into factual retrieval.
- Redesigning catalog administration, changing immediate Save activation, public/private Storage policy or the existing knowledge publication workflow.
- A new delivery queue, messaging service, unconstrained URL generation or automatic replay of uncertain provider requests.
- Adding media support to legacy Fonnte.
- Unrelated authentication/session changes already present in the worktree.
- Production deployment, customer rollout or paid evaluations merely as a consequence of publishing this specification.

## Further Notes

The user approved the request-only policy, unrestricted successive explicit requests with one image per reply, image-first ordering followed by a separate relevant price/detail message, and conservative failure handling on 22 October 2026. These decisions supersede the earlier automatic-image and text-first behavior.

The prior read-only readiness audit found an enabled 27-asset catalog and a working WAHA GOWS session, but the canonical production application pointed to a release preceding catalog implementation. Treat that as a timestamped observation, not a guarantee of current deployment state. Recheck deployment and worker evidence before claiming WhatsApp production completion. Existing WAHA image sending and public catalog URLs do not require a separate image-enable switch.

The images are approved illustrations, not authenticated stock photographs. Retain that qualification and all physical-variant limitations. This specification is ready for agent implementation; publishing it does not change runtime behavior or infrastructure.
