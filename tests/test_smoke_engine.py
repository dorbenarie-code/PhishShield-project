"""
Smoke tests for PhishShield engine.

Verifies that the Analyzer loads correctly and detects obvious phishing signals.
"""
from __future__ import annotations

import pytest

from app.core.analyzer import Analyzer


class TestSmokeEngine:
    """Basic smoke tests to verify the engine works end-to-end."""

    @pytest.fixture
    def analyzer(self) -> Analyzer:
        """Create an Analyzer instance with the default rule pack."""
        return Analyzer()

    def test_analyzer_loads_successfully(self, analyzer: Analyzer) -> None:
        """Verify that the Analyzer and RuleEngine load without errors."""
        assert analyzer is not None
        assert analyzer.engine is not None
        assert len(analyzer.engine.rules) > 0, "Expected at least one rule to be loaded"

    def test_detects_phishing_signals(self, analyzer: Analyzer) -> None:
        """
        Send text containing obvious phishing signals:
        - Hebrew urgency word "דחוף" (urgent)
        - Suspicious shortened URL (bit.ly)
        
        Expect:
        - score > 0
        - len(hits) >= 1
        - highlights present
        """
        phishing_text = """
        שלום,
        
        הודעה דחוף! החשבון שלך יינעל תוך 24 שעות.
        לחץ כאן כדי לאמת את החשבון שלך:
        https://bit.ly/3xYz123
        
        בברכה,
        צוות התמיכה
        """
        
        result = analyzer.analyze(body=phishing_text)
        
        # Verify score is positive (phishing detected)
        assert result.score > 0, f"Expected score > 0, got {result.score}"
        
        # Verify at least one rule hit
        assert len(result.hits) >= 1, f"Expected at least 1 hit, got {len(result.hits)}"
        
        # Verify highlights are present
        assert len(result.highlights) > 0, f"Expected highlights, got {len(result.highlights)}"
        
        # Print details for debugging (visible with pytest -v)
        print(f"\n  Score: {result.score}")
        print(f"  Severity: {result.severity}")
        print(f"  Hits: {len(result.hits)}")
        for hit in result.hits:
            print(f"    - {hit.rule_id}: {hit.title} (weight={hit.weight})")
        print(f"  Highlights: {len(result.highlights)}")

    def test_benign_text_low_score(self, analyzer: Analyzer) -> None:
        """Verify that normal/benign text has a low score."""
        benign_text = """
        שלום דני,
        
        תודה על הפגישה אתמול. היה נחמד לדבר איתך.
        נתראה בשבוע הבא.
        
        בברכה,
        יוסי
        """
        
        result = analyzer.analyze(body=benign_text)
        
        # Benign text should have a low score (may not be 0 due to some generic patterns)
        # but definitely shouldn't be flagged as high-risk
        assert result.score < 50, f"Expected low score for benign text, got {result.score}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

