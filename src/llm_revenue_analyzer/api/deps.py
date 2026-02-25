from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from llm_revenue_analyzer.core.settings import Settings, get_settings
from llm_revenue_analyzer.pricing import CostCalculator, PricingCatalog
from llm_revenue_analyzer.store.db import get_db_session


@lru_cache(maxsize=4)
def _load_pricing_catalog(pricing_path: str) -> PricingCatalog:
    return PricingCatalog.from_yaml(Path(pricing_path))


def get_pricing_catalog(settings: Settings = Depends(get_settings)) -> PricingCatalog:
    return _load_pricing_catalog(str(settings.pricing_path))


def get_cost_calculator(catalog: PricingCatalog = Depends(get_pricing_catalog)) -> CostCalculator:
    return CostCalculator(catalog)


def get_session(session: Session = Depends(get_db_session)) -> Session:
    return session
