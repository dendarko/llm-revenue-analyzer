from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml


class PricingError(Exception):
    pass


class PricingNotFound(PricingError):
    pass


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    input_per_1k_tokens: Decimal
    output_per_1k_tokens: Decimal
    currency: str = "USD"


class PricingCatalog:
    def __init__(self, models: dict[tuple[str, str], ModelPricing]) -> None:
        self._models = models

    def get(self, provider: str, model: str) -> ModelPricing:
        key = (provider.lower(), model.lower())
        if key not in self._models:
            raise PricingNotFound(f"No pricing configured for provider={provider} model={model}")
        return self._models[key]

    @classmethod
    def from_yaml(cls, path: Path) -> PricingCatalog:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "providers" not in raw:
            raise PricingError("pricing.yaml must contain top-level 'providers'")

        models: dict[tuple[str, str], ModelPricing] = {}
        providers = raw.get("providers", {})
        if not isinstance(providers, dict):
            raise PricingError("'providers' must be a mapping")

        for provider_name, provider_data in providers.items():
            if not isinstance(provider_data, dict):
                raise PricingError(f"provider {provider_name} must be a mapping")
            provider_models = provider_data.get("models", {})
            if not isinstance(provider_models, dict):
                raise PricingError(f"provider {provider_name}.models must be a mapping")
            for model_name, model_data in provider_models.items():
                if not isinstance(model_data, dict):
                    raise PricingError(f"model entry for {provider_name}/{model_name} must be a mapping")
                models[(str(provider_name).lower(), str(model_name).lower())] = ModelPricing(
                    provider=str(provider_name),
                    model=str(model_name),
                    input_per_1k_tokens=Decimal(str(model_data["input_per_1k_tokens"])),
                    output_per_1k_tokens=Decimal(str(model_data["output_per_1k_tokens"])),
                    currency=str(model_data.get("currency", "USD")),
                )
        return cls(models)


class CostCalculator:
    def __init__(self, catalog: PricingCatalog) -> None:
        self.catalog = catalog

    def compute_cost_usd(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Decimal:
        pricing = self.catalog.get(provider=provider, model=model)
        prompt_cost = (Decimal(prompt_tokens) / Decimal(1000)) * pricing.input_per_1k_tokens
        completion_cost = (Decimal(completion_tokens) / Decimal(1000)) * pricing.output_per_1k_tokens
        total = prompt_cost + completion_cost
        return total.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
