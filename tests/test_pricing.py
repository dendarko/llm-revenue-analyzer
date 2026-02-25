from __future__ import annotations

from pathlib import Path

from llm_revenue_analyzer.pricing import CostCalculator, PricingCatalog


def test_pricing_cost_calculation() -> None:
    catalog = PricingCatalog.from_yaml(Path("data/pricing.yaml"))
    calc = CostCalculator(catalog)
    cost = calc.compute_cost_usd(
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=1000,
    )
    assert float(cost) == 0.00075
