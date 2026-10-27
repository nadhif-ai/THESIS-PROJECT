export const NINEROUTER_MODELS = [
  "azure/gpt-5.6-terra-20260709-global",
  "azure/gpt-5.6-luna-20260709-global",
  "cx/gpt-6-luna[1m]",
  "glm/glm-5.3-flash",
];

export const NINEROUTER_MODEL_OPTIONS = NINEROUTER_MODELS.map((model) => `9router::${model}`);

export function providerModelLabel(model: string) {
  return model.startsWith("9router::")
    ? `9Router · ${model.slice("9router::".length)}`
    : `OpenRouter · ${model}`;
}
