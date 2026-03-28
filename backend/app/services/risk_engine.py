"""Risk analysis engine - identifies risk flags from extracted spec data."""

import re

from app.schemas.analysis import (
    SpecExtraction,
    RiskFlag,
    RiskReport,
    RiskSeverity,
    RiskType,
)


class RiskEngine:
    """
    Engine for analyzing extracted spec data and generating risk flags.
    Uses rule-based analysis; TODO: enhance with ML/LLM scoring.
    """

    def analyze(self, extraction: SpecExtraction, raw_text: str | None = None) -> RiskReport:
        """
        Analyze extracted data and generate risk report.
        """
        flags = []

        # Check warranty risks
        warranty_flag = self._check_warranty(extraction.warranty_requirements)
        if warranty_flag:
            flags.append(warranty_flag)

        # Check liquidated damages risks
        ld_flag = self._check_liquidated_damages(extraction.liquidated_damages)
        if ld_flag:
            flags.append(ld_flag)

        # Check bonding risks
        bonding_flag = self._check_bonding(extraction.bonding_requirements)
        if bonding_flag:
            flags.append(bonding_flag)

        # Check insurance risks
        insurance_flag = self._check_insurance(extraction.insurance_requirements)
        if insurance_flag:
            flags.append(insurance_flag)

        # Check testing/commissioning burden
        testing_flag = self._check_testing(extraction.testing_requirements, extraction.commissioning_requirements)
        if testing_flag:
            flags.append(testing_flag)

        # Calculate overall risk level
        overall_level = self._calculate_overall_risk(flags)

        # Generate summary
        summary = self._generate_summary(flags, overall_level)

        return RiskReport(
            overall_risk_level=overall_level,
            overall_summary=summary,
            flags=flags,
            total_flags=len(flags),
            high_severity_count=sum(1 for f in flags if f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]),
        )

    def _check_warranty(self, warranty_text: str | None) -> RiskFlag | None:
        """Check for warranty-related risks."""
        if not warranty_text:
            return None

        # Look for warranty duration
        duration_match = re.search(r"(\d+)\s*(?:year|yr)", warranty_text, re.IGNORECASE)

        if duration_match:
            years = int(duration_match.group(1))

            if years >= 5:
                return RiskFlag(
                    type=RiskType.WARRANTY,
                    severity=RiskSeverity.HIGH,
                    title="Extended Warranty Required",
                    description=f"Warranty period of {years} years exceeds typical 1-2 year standard. Extended warranty obligations increase long-term liability exposure.",
                    source_text=warranty_text[:200],
                )
            elif years >= 2:
                return RiskFlag(
                    type=RiskType.WARRANTY,
                    severity=RiskSeverity.MEDIUM,
                    title="Above-Standard Warranty",
                    description=f"Warranty period of {years} years is above typical 1-year standard. Review warranty terms carefully.",
                    source_text=warranty_text[:200],
                )

        return None

    def _check_liquidated_damages(self, ld_text: str | None) -> RiskFlag | None:
        """Check for liquidated damages risks."""
        if not ld_text:
            return None

        # Look for dollar amounts
        amount_match = re.search(r"\$\s*([\d,]+)", ld_text)

        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            try:
                amount = int(amount_str)

                if amount >= 1000:
                    return RiskFlag(
                        type=RiskType.PENALTY,
                        severity=RiskSeverity.CRITICAL,
                        title="High Liquidated Damages",
                        description=f"Liquidated damages of ${amount:,}/day identified. Significant financial exposure for schedule delays.",
                        source_text=ld_text[:200],
                    )
                elif amount >= 500:
                    return RiskFlag(
                        type=RiskType.PENALTY,
                        severity=RiskSeverity.HIGH,
                        title="Significant Liquidated Damages",
                        description=f"Liquidated damages of ${amount:,}/day identified. Review schedule buffer requirements.",
                        source_text=ld_text[:200],
                    )
                elif amount > 0:
                    return RiskFlag(
                        type=RiskType.PENALTY,
                        severity=RiskSeverity.MEDIUM,
                        title="Liquidated Damages Present",
                        description=f"Liquidated damages of ${amount:,}/day identified.",
                        source_text=ld_text[:200],
                    )
            except ValueError:
                pass

        # Even without amount, LD language is a concern
        return RiskFlag(
            type=RiskType.PENALTY,
            severity=RiskSeverity.MEDIUM,
            title="Liquidated Damages Clause",
            description="Liquidated damages clause identified. Review specific amounts and conditions.",
            source_text=ld_text[:200] if ld_text else None,
        )

    def _check_bonding(self, bonding_text: str | None) -> RiskFlag | None:
        """Check for bonding requirements."""
        if not bonding_text:
            return None

        bonding_lower = bonding_text.lower()

        # Check for performance bond
        has_performance = "performance bond" in bonding_lower
        has_payment = "payment bond" in bonding_lower
        has_bid = "bid bond" in bonding_lower

        if has_performance and has_payment:
            return RiskFlag(
                type=RiskType.BONDING,
                severity=RiskSeverity.HIGH,
                title="Full Bonding Required",
                description="Performance and payment bonds required. Ensure bonding capacity and factor bond costs into bid.",
                source_text=bonding_text[:200],
            )
        elif has_performance or has_payment:
            return RiskFlag(
                type=RiskType.BONDING,
                severity=RiskSeverity.MEDIUM,
                title="Bonding Required",
                description="Bond requirements identified. Review specific bonding requirements and costs.",
                source_text=bonding_text[:200],
            )
        elif has_bid:
            return RiskFlag(
                type=RiskType.BONDING,
                severity=RiskSeverity.LOW,
                title="Bid Bond Required",
                description="Bid bond required for proposal submission.",
                source_text=bonding_text[:200],
            )

        return RiskFlag(
            type=RiskType.BONDING,
            severity=RiskSeverity.LOW,
            title="Bonding Language Present",
            description="Bonding/surety language identified. Review specific requirements.",
            source_text=bonding_text[:200],
        )

    def _check_insurance(self, insurance_text: str | None) -> RiskFlag | None:
        """Check for insurance requirements."""
        if not insurance_text:
            return None

        # Look for high coverage amounts
        amount_match = re.search(r"\$\s*([\d,]+)\s*(?:million|M)", insurance_text, re.IGNORECASE)

        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            try:
                amount_millions = float(amount_str)

                if amount_millions >= 5:
                    return RiskFlag(
                        type=RiskType.INSURANCE,
                        severity=RiskSeverity.HIGH,
                        title="High Insurance Requirements",
                        description=f"Insurance coverage of ${amount_millions}M+ required. Verify coverage limits and costs.",
                        source_text=insurance_text[:200],
                    )
                elif amount_millions >= 2:
                    return RiskFlag(
                        type=RiskType.INSURANCE,
                        severity=RiskSeverity.MEDIUM,
                        title="Elevated Insurance Requirements",
                        description=f"Insurance coverage of ${amount_millions}M required.",
                        source_text=insurance_text[:200],
                    )
            except ValueError:
                pass

        return None

    def _check_testing(self, testing_text: str | None, commissioning_text: str | None) -> RiskFlag | None:
        """Check for testing and commissioning burden."""
        has_tab = False
        has_cx = False
        has_third_party = False

        if testing_text:
            testing_lower = testing_text.lower()
            has_tab = "tab" in testing_lower or "testing, adjusting" in testing_lower or "testing and balancing" in testing_lower
            has_third_party = "third party" in testing_lower or "independent" in testing_lower

        if commissioning_text:
            cx_lower = commissioning_text.lower()
            has_cx = any(term in cx_lower for term in ["commission", "cx", "functional performance"])

        if has_cx and has_third_party:
            return RiskFlag(
                type=RiskType.COMMISSIONING,
                severity=RiskSeverity.HIGH,
                title="Third-Party Commissioning Required",
                description="Third-party commissioning requirements identified. Budget for CxA coordination and testing time.",
                source_text=(commissioning_text or testing_text or "")[:200],
            )
        elif has_cx:
            return RiskFlag(
                type=RiskType.COMMISSIONING,
                severity=RiskSeverity.MEDIUM,
                title="Commissioning Required",
                description="Commissioning requirements identified. Review Cx scope and coordination needs.",
                source_text=(commissioning_text or "")[:200],
            )
        elif has_tab:
            return RiskFlag(
                type=RiskType.TESTING,
                severity=RiskSeverity.LOW,
                title="TAB Requirements",
                description="Testing, Adjusting, and Balancing (TAB) requirements identified.",
                source_text=(testing_text or "")[:200],
            )

        return None

    def _calculate_overall_risk(self, flags: list[RiskFlag]) -> RiskSeverity:
        """Calculate overall risk level from individual flags."""
        if not flags:
            return RiskSeverity.LOW

        # Count by severity
        critical_count = sum(1 for f in flags if f.severity == RiskSeverity.CRITICAL)
        high_count = sum(1 for f in flags if f.severity == RiskSeverity.HIGH)
        medium_count = sum(1 for f in flags if f.severity == RiskSeverity.MEDIUM)

        if critical_count > 0:
            return RiskSeverity.CRITICAL
        elif high_count >= 2:
            return RiskSeverity.CRITICAL
        elif high_count >= 1:
            return RiskSeverity.HIGH
        elif medium_count >= 2:
            return RiskSeverity.HIGH
        elif medium_count >= 1:
            return RiskSeverity.MEDIUM
        else:
            return RiskSeverity.LOW

    def _generate_summary(self, flags: list[RiskFlag], overall_level: RiskSeverity) -> str:
        """Generate overall risk summary."""
        if not flags:
            return "No significant risks identified in document analysis."

        risk_types = list(set(f.type.value for f in flags))
        high_risks = [f for f in flags if f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]]

        summary_parts = [f"Overall risk level: {overall_level.value.upper()}."]
        summary_parts.append(f"Identified {len(flags)} risk flag(s) across: {', '.join(risk_types)}.")

        if high_risks:
            summary_parts.append(f"Key concerns: {', '.join(f.title for f in high_risks[:3])}.")

        return " ".join(summary_parts)


# Singleton instance
risk_engine = RiskEngine()
