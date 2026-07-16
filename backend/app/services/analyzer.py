"""Deterministic creative performance rule engine."""

from dataclasses import dataclass
from decimal import Decimal

from app.models import CreativeStatus


@dataclass(frozen=True, slots=True)
class AnalyzerThresholds:
    ctr_drop_pct: Decimal
    cpa_increase_pct: Decimal
    minimum_roas: Decimal
    maximum_frequency: Decimal
    spend_threshold: Decimal


@dataclass(frozen=True, slots=True)
class Performance:
    spend: Decimal
    revenue: Decimal
    impressions: int
    clicks: int
    purchases: int
    reach: int = 0

    @property
    def ctr(self) -> Decimal:
        return Decimal(self.clicks * 100) / self.impressions if self.impressions else Decimal(0)

    @property
    def cpa(self) -> Decimal | None:
        return self.spend / self.purchases if self.purchases else None

    @property
    def roas(self) -> Decimal:
        return self.revenue / self.spend if self.spend else Decimal(0)

    @property
    def frequency(self) -> Decimal:
        return Decimal(self.impressions) / self.reach if self.reach else Decimal(0)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    status: CreativeStatus
    reasons: tuple[str, ...]
    critical: bool


def percent_change(current: Decimal, baseline: Decimal) -> Decimal | None:
    """Return signed percentage change, or None when baseline is zero."""

    if baseline == 0:
        return None
    return ((current - baseline) / baseline) * Decimal(100)


def analyze(
    current: Performance, baseline: Performance | None, thresholds: AnalyzerThresholds
) -> AnalysisResult:
    """Classify a creative using transparent, configurable business rules."""

    reasons: list[str] = []
    critical = False
    ctr_change = percent_change(current.ctr, baseline.ctr) if baseline else None
    cpa_change = (
        percent_change(current.cpa, baseline.cpa)
        if baseline and current.cpa is not None and baseline.cpa is not None
        else None
    )

    if ctr_change is not None and ctr_change < -thresholds.ctr_drop_pct:
        reasons.append(f"CTR down {abs(ctr_change):.1f}%")
    if cpa_change is not None and cpa_change > thresholds.cpa_increase_pct:
        reasons.append(f"CPA up {cpa_change:.1f}%")
    if current.spend > 0 and current.roas < thresholds.minimum_roas:
        reasons.append(f"ROAS {current.roas:.2f} below target {thresholds.minimum_roas:.2f}")
    if baseline and current.frequency > thresholds.maximum_frequency and current.ctr < baseline.ctr:
        reasons.append(
            f"Frequency {current.frequency:.2f} above "
            f"{thresholds.maximum_frequency:.2f} with CTR declining"
        )
    if current.spend > thresholds.spend_threshold and current.purchases == 0:
        reasons.append(f"Spend {current.spend:.2f} with zero purchases")
        critical = True

    if critical or len(reasons) >= 2:
        status = CreativeStatus.TURN_OFF_RECOMMENDATION
    elif reasons:
        status = CreativeStatus.WATCH
    else:
        status = CreativeStatus.HEALTHY
    return AnalysisResult(status=status, reasons=tuple(reasons), critical=critical)
