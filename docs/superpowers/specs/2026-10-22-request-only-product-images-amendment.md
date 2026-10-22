# Request-only product images

Date: 2026-10-22, Asia/Jakarta.

Status: approved by the user's final shared-understanding confirmation on 2026-10-22. Request-only attachments, successive requests with one image per reply, image-first ordering followed by a separate price/detail message, and delivery fallback are agreed. No runtime changes made during this refinement.

This amendment supersedes the automatic new-product/comparison attachment policy and text-first ordering in `2026-10-22-context-aware-product-images-design.md`. Other approved boundaries continue unless explicitly changed.

## Confirmed change

Attach catalog images only when the customer requests a visual. A new product, price inquiry, material inquiry or textual comparison alone must not attach an image. Successive explicit requests may target different products or ask to see a previous illustration again. A repeated explicit request must not be blocked by automatic repetition suppression; uncertain old delivery jobs still must not be replayed automatically.

Keep at most one image per reply. A multi-product visual request uses a suitable single comparison image or asks which product to show first. It does not send an arbitrary image or several separate images.

For a matched image request, show/send the illustration first, followed by a separate text message beneath it containing concise, relevant prices and product details from active knowledge. The customer does not need to ask for price again. If price depends on an unspecified size/material, explain the relevant options or ask for the missing detail; do not invent a single exact quote. A short image caption identifies the illustration rather than duplicating the price explanation. Playground must render the same image-before-details sequence.

## Reproduced behavior and causes

The current selector reproduces the user's screenshot:

1. `Hi kak mau print banner dong` selects the banner hero as `new_product` under the original policy.
2. `Mau liat yg banner x tegak` retains generic banner focus; reversed `banner x` is missing from stand aliases.
3. `Iyaa kak X-banner, kirimin preview gambarnya dulu dong` selects the X-banner hero as `new_product`, with `explicit=False` because the regex matches only complete words `gambar|foto|contoh|visual`.

`app/backend/chain.py` currently invokes the answering model before selecting the image. `app/backend/prompt_template.py` tells it to use photo URLs from factual knowledge. The model therefore cannot acknowledge the actual catalog attachment and may deny availability before an image is subsequently selected.

## Proposed correction

- Recognize Indonesian suffixes and common visual wording: `gambarnya`, `fotonya`, `preview`, and contextual `mau lihat/liat`. Respect explicit negation or text-only requests. Bare `kirim` in a shipping question must remain nonvisual.
- Recognize reversed stand aliases `banner x` and `banner y`, replacing generic banner focus when a stand is identified.
- Resolve the catalog decision before answer generation. Supply a narrow trusted attachment status and product label to the answer prompt; keep catalog descriptions out of factual price/specification context.
- When an illustration is selected, compose relevant price/product details from active knowledge to follow the image. Do not invent an external photo link or claim delivery before the provider outcome is known.
- When no appropriate image exists, clarify ambiguity or state the actual catalog limitation. Do not attach an unrelated hero, claim an exact unpictured variant, or deny availability while attaching a selected illustration.
- Persist the coordinated answer, selected asset and focus atomically under the existing inbox lease; suppress media if generation fails. Change transport to image first, then the detail message, retaining independent checkpoints and no automatic replay of uncertain parts. A failed or uncertain image must not erase the available price/details text or cause an automatic duplicate image. Definitive failures on explicit requests receive the existing brief failure notice.
- Apply the requested-only policy consistently to automatic legacy `[MEDIA]` attachments as well as catalog selection, preventing fallback from bypassing the policy.
- Playground decision reasons should identify explicit image requests, ambiguity, unpictured variants, or no image requested; `new_product` must no longer be an attachment trigger.

## Final shared-understanding checkpoint

The user confirmed the combined contract on 2026-10-22: unrestricted successive explicit requests, one image per reply, image-first ordering with a separate relevant price/detail message below, preserving the available detail text if image delivery fails, and never automatically resending an uncertain image. The interview is complete; this amendment is the agreed basis for implementation.

## Verification required after design agreement

Use the exact screenshot conversation as a regression. Also cover plain product/price/material/text-comparison questions without media; `gambarnya`/`fotonya`/preview/slang; reversed aliases; successive different products; explicit same-image resend; implicit product context; negation; unsupported variants; contradictory unavailable wording; identical Playground and WAHA selection and image-before-details ordering; prices grounded in active knowledge; and per-part recovery without automatically retrying uncertain sends.

## Live readiness audit

Read-only project-scoped inspection on 2026-10-22 found the catalog feature enabled (revision 28), 27 enabled assets, public catalog Storage, and private staging/original buckets. WAHA reported WORKING with a connected GOWS engine; webhook events include message and message.ack. No customer message was sent during this refinement audit. Deployment/worker evidence and customer-facing delivery must be distinguished from these readiness signals.

The canonical webhook host `https://chatbotta-nadhif.vercel.app` reports healthy, but its OpenAPI does not expose the catalog routes. Vercel's production alias points to commit `74270180`, before catalog implementation `69444d8`. The catalog database switch alone therefore does not activate this feature in production WhatsApp. Deploy the corrected application before performing a controlled customer-channel verification. No separate WAHA image switch is required; GOWS supports `/api/sendImage` with the public catalog URL. See [official WAHA media documentation](https://waha.devlike.pro/docs/how-to/send-messages/).
