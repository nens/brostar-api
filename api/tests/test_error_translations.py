from api.signals import translate_bro_error


class TestBroErrorTranslations:
    """Test suite for BRO error message translations."""

    def test_static_error_translation_formation_resistance(self):
        """Test static translation for FormationResistanceDetermination error."""
        error_message = (
            "FormationResistanceDetermination.determinationType) moet aanwezig zijn"
        )
        expected = "De meetconfiguraties voor dit Formatieweerstandsdossier zijn nog niet aangeleverd. Lever eerst de meetconfiguraties aan."

        result = translate_bro_error(error_message)
        assert result == expected

    def test_static_error_translation_partial_match(self):
        """Test that static translations work with partial error message match."""
        error_message = "Some prefix: FormationResistanceDetermination.determinationType) moet aanwezig zijn and more"
        expected = "De meetconfiguraties voor dit Formatieweerstandsdossier zijn nog niet aangeleverd. Lever eerst de meetconfiguraties aan."

        result = translate_bro_error(error_message)
        assert result == expected

    def test_dynamic_error_translation_positioning_measuring(self):
        """Test dynamic translation for PositionsMeasuring duplicate event error."""
        error_message = "De combinatie van Posities inmeten.naam gebeurtenis (PositionsMeasuring.eventName) = nieuweInmetingPosities op Posities inmeten.datum gebeurtenis (PositionsMeasuring.eventDate) = (2025-07-03, JJJJ-MM-DD) is niet correct: Er is reeds een zelfde gebeurtenis op deze datum geregistreerd."
        expected = "Er is al een nieuweInmetingPosities geregistreerd op 2025-07-03."

        result = translate_bro_error(error_message)
        assert result == expected

    def test_dynamic_error_translation_different_event_and_date(self):
        """Test dynamic translation with different eventName and eventDate values."""
        error_message = "De combinatie van Posities inmeten.naam gebeurtenis (PositionsMeasuring.eventName) = andereMeting op Posities inmeten.datum gebeurtenis (PositionsMeasuring.eventDate) = (2024-12-15, JJJJ-MM-DD) is niet correct: Er is reeds een zelfde gebeurtenis op deze datum geregistreerd."
        expected = "Er is al een andereMeting geregistreerd op 2024-12-15."

        result = translate_bro_error(error_message)
        assert result == expected

    def test_empty_error_message(self):
        """Test that empty error message is returned as-is."""
        result = translate_bro_error("")
        assert result == ""

    def test_none_error_message(self):
        """Test that None error message is handled gracefully."""
        result = translate_bro_error(None)
        assert result is None

    def test_unknown_error_message(self):
        """Test that unknown error message is returned unchanged."""
        error_message = "Unknown error that does not match any pattern"
        result = translate_bro_error(error_message)
        assert result == error_message

    def test_error_priority_static_over_dynamic(self):
        """Test that static translations are checked before dynamic patterns."""
        # If an error contains both a static pattern and dynamic pattern,
        # the static one should win
        error_message = (
            "FormationResistanceDetermination.determinationType) moet aanwezig zijn"
        )
        expected = "De meetconfiguraties voor dit Formatieweerstandsdossier zijn nog niet aangeleverd. Lever eerst de meetconfiguraties aan."

        result = translate_bro_error(error_message)
        assert result == expected
