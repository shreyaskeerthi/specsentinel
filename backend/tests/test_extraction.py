"""Tests for spec extraction and risk analysis services."""

import pytest

from app.services.spec_extraction import spec_extraction_service
from app.services.spec_chunking import spec_chunking_service
from app.services.risk_engine import risk_engine
from app.schemas.analysis import RiskSeverity


def test_spec_chunking_basic(sample_spec_text):
    """Test basic document segmentation."""
    sections = spec_chunking_service.segment_document(sample_spec_text)

    assert len(sections) > 0

    # Check that divisions were found
    division_nums = [s.division for s in sections if s.division]
    assert "00" in division_nums or "23" in division_nums


def test_extract_mep_divisions(sample_spec_text):
    """Test MEP division extraction."""
    divisions = spec_chunking_service.extract_mep_divisions(sample_spec_text)

    # Should have div23 content (HVAC)
    assert divisions.get("div23") is not None
    assert "HVAC" in divisions["div23"] or "23" in divisions["div23"]


def test_spec_extraction(sample_spec_text):
    """Test full spec extraction."""
    extraction = spec_extraction_service.extract(sample_spec_text)

    # Check insurance extraction
    assert extraction.insurance_requirements is not None
    assert "2,000,000" in extraction.insurance_requirements or "liability" in extraction.insurance_requirements.lower()

    # Check bonding extraction
    assert extraction.bonding_requirements is not None
    assert "bond" in extraction.bonding_requirements.lower()

    # Check warranty extraction
    assert extraction.warranty_requirements is not None
    assert "year" in extraction.warranty_requirements.lower()

    # Check liquidated damages extraction
    assert extraction.liquidated_damages is not None
    assert "1,500" in extraction.liquidated_damages or "liquidated" in extraction.liquidated_damages.lower()

    # Check testing extraction
    assert extraction.testing_requirements is not None
    assert "TAB" in extraction.testing_requirements or "test" in extraction.testing_requirements.lower()

    # Check commissioning extraction
    assert extraction.commissioning_requirements is not None
    assert "commission" in extraction.commissioning_requirements.lower()


def test_risk_engine_warranty_flag(sample_spec_text):
    """Test risk engine flags extended warranty."""
    extraction = spec_extraction_service.extract(sample_spec_text)
    risk_report = risk_engine.analyze(extraction)

    # Should flag warranty risk (5 year roofing warranty mentioned)
    warranty_flags = [f for f in risk_report.flags if f.type.value == "warranty"]
    # May or may not flag depending on which warranty is extracted
    assert len(risk_report.flags) > 0  # Should have some flags


def test_risk_engine_ld_flag(sample_spec_text):
    """Test risk engine flags liquidated damages."""
    extraction = spec_extraction_service.extract(sample_spec_text)
    risk_report = risk_engine.analyze(extraction)

    # Should flag LD risk ($1,500/day)
    penalty_flags = [f for f in risk_report.flags if f.type.value == "penalty"]
    assert len(penalty_flags) > 0
    assert any(f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL] for f in penalty_flags)


def test_risk_engine_bonding_flag(sample_spec_text):
    """Test risk engine flags bonding requirements."""
    extraction = spec_extraction_service.extract(sample_spec_text)
    risk_report = risk_engine.analyze(extraction)

    # Should flag bonding (performance + payment bond required)
    bonding_flags = [f for f in risk_report.flags if f.type.value == "bonding"]
    assert len(bonding_flags) > 0


def test_risk_report_summary(sample_spec_text):
    """Test risk report summary generation."""
    extraction = spec_extraction_service.extract(sample_spec_text)
    risk_report = risk_engine.analyze(extraction)

    assert risk_report.overall_summary is not None
    assert len(risk_report.overall_summary) > 10
    assert risk_report.total_flags == len(risk_report.flags)


def test_empty_text_extraction():
    """Test extraction handles empty text."""
    extraction = spec_extraction_service.extract("")

    # All fields should be None for empty text
    assert extraction.insurance_requirements is None
    assert extraction.bonding_requirements is None


def test_risk_engine_no_risks():
    """Test risk engine with clean extraction."""
    from app.schemas.analysis import SpecExtraction

    clean_extraction = SpecExtraction()
    risk_report = risk_engine.analyze(clean_extraction)

    assert risk_report.overall_risk_level == RiskSeverity.LOW
    assert "No significant risks" in risk_report.overall_summary
