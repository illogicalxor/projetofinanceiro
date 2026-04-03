"""Tests for projetofinanceiro core module."""

import pytest
from datetime import datetime

from projetofinanceiro.core import (
    _normalise_ticker,
    backtest_dca,
    backtest_lump_sum,
    get_ipca_anual,
    get_selic_rates,
    simulate_tesouro_selic,
)


# ---------------------------------------------------------------------------
# Ticker normalisation
# ---------------------------------------------------------------------------


class TestNormaliseTicker:
    def test_adds_sa_suffix(self):
        assert _normalise_ticker("WEGE3") == "WEGE3.SA"

    def test_keeps_existing_suffix(self):
        assert _normalise_ticker("WEGE3.SA") == "WEGE3.SA"

    def test_us_ticker_unchanged(self):
        assert _normalise_ticker("AAPL") == "AAPL"

    def test_strips_and_uppercases(self):
        assert _normalise_ticker("  wege3  ") == "WEGE3.SA"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _normalise_ticker("")


# ---------------------------------------------------------------------------
# Backtest DCA — smoke tests (require network)
# ---------------------------------------------------------------------------


@pytest.mark.network
class TestBacktestDCA:
    def test_basic_dca(self):
        result = backtest_dca("WEGE3", monthly_investment=1000,
                              start="2020-01-01", end="2024-12-31")
        assert result["ticker"] == "WEGE3.SA"
        assert result["patrimonio_final"] > 0
        assert result["total_investido"] > 0
        assert result["data_inicio_real"] is not None

    def test_invalid_ticker_raises(self):
        with pytest.raises(ValueError):
            backtest_dca("INVALIDTICKERXYZ", start="2020-01-01", end="2024-12-31")


# ---------------------------------------------------------------------------
# Backtest Lump Sum — smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.network
class TestBacktestLumpSum:
    def test_basic_lump_sum(self):
        result = backtest_lump_sum("WEGE3", initial_investment=10000,
                                   start="2020-01-01", end="2024-12-31")
        assert result["ticker"] == "WEGE3.SA"
        assert result["patrimonio_final"] > 0
        assert result["total_investido"] == 10000


# ---------------------------------------------------------------------------
# IPCA
# ---------------------------------------------------------------------------


@pytest.mark.network
class TestIPCA:
    def test_returns_dataframe(self):
        df = get_ipca_anual("01/01/2020", "31/12/2024")
        assert not df.empty
        assert "ano" in df.columns
        assert "inflacao_acumulada" in df.columns


# ---------------------------------------------------------------------------
# Selic
# ---------------------------------------------------------------------------


@pytest.mark.network
class TestSelic:
    def test_get_rates(self):
        df = get_selic_rates("2020-01-01")
        assert not df.empty
        assert "valor" in df.columns

    def test_simulate(self):
        result = simulate_tesouro_selic("2020-01-01", monthly_investment=1000)
        assert result["patrimonio_final"] > 0
        assert result["total_aportes"] > 0
        assert not result["evolucao"].empty
