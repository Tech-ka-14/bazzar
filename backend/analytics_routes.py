"""P7-C analytics endpoints (roadmap 7.3).

Thin HTTP layer over ``backend/analytics.py``; mounted in ``server.py`` on
both ``/api/v1`` and the deprecated ``/api`` alias, exactly like the main
router. Error mapping:

* unknown symbol            → 404 ``not_found`` envelope
* unknown method/model, bad confidence, bad weights → 400 ``bad_request``
  envelope (message lists the valid options)
* insufficient history      → 422 ``insufficient_data`` envelope (the number
  is never fabricated)
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import closing
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from . import analytics, schemas
from .db import get_connection
from .middleware import error_envelope

router = APIRouter()


def _run(compute: Callable[[], dict[str, Any]]) -> dict[str, Any] | JSONResponse:
    """Execute a service call, mapping domain errors onto the envelope."""
    try:
        return compute()
    except analytics.UnknownSymbolError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except analytics.InsufficientDataError as exc:
        return JSONResponse(
            status_code=422,
            content=error_envelope("insufficient_data", str(exc)),
        )
    except KeyError as exc:
        # quant.api-style "unknown X 'foo'; available: [...]" message.
        raise HTTPException(status_code=400, detail=str(exc.args[0])) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analytics/var", response_model=schemas.VarResponse)
def analytics_var(
    symbol: str = Query(..., min_length=1),
    method: str = "historical",
    confidence: float = 0.99,
) -> dict[str, Any] | JSONResponse:
    with closing(get_connection()) as con:
        return _run(lambda: analytics.get_var(con, symbol, method, confidence))


@router.get("/analytics/volatility", response_model=schemas.VolatilityResponse)
def analytics_volatility(
    symbol: str = Query(..., min_length=1),
    model: str = "ewma",
) -> dict[str, Any] | JSONResponse:
    with closing(get_connection()) as con:
        return _run(lambda: analytics.get_volatility(con, symbol, model))


@router.post("/analytics/portfolio/risk", response_model=schemas.PortfolioRiskResponse)
def analytics_portfolio_risk(
    body: schemas.PortfolioRiskRequest,
) -> dict[str, Any] | JSONResponse:
    with closing(get_connection()) as con:
        return _run(lambda: analytics.get_portfolio_risk(con, body.weights, body.confidence))


@router.get("/analytics/backtest/var", response_model=schemas.VarBacktestResponse)
def analytics_var_backtest(
    symbol: str = Query(..., min_length=1),
    confidence: float = 0.99,
) -> dict[str, Any] | JSONResponse:
    with closing(get_connection()) as con:
        return _run(lambda: analytics.get_var_backtest(con, symbol, confidence))
