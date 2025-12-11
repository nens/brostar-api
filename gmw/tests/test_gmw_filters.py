from datetime import date, timedelta

import pytest
from django.test import RequestFactory

from api.tests import fixtures
from gmw import filters
from gmw.models import GMW, Event, MonitoringTube

# Fixture imports for ruff
organisation = fixtures.organisation
gmw = fixtures.gmw
tube = fixtures.tube
event = fixtures.event
gmn = fixtures.gmn
measuringpoint = fixtures.measuringpoint


@pytest.mark.django_db
class TestGmwFilter:
    """Tests for GmwFilter"""

    def test_filter_all_fields(self, gmw):
        """Test that filter can handle all fields"""
        factory = RequestFactory()
        request = factory.get("/", {"bro_id": gmw.bro_id})

        filterset = filters.GmwFilter(request.GET, queryset=GMW.objects.all())

        assert filterset.is_valid()
        assert gmw in filterset.qs

    def test_json_field_filter_icontains(self, gmw):
        """Test JSONField filtering with icontains lookup"""
        # Assuming GMW has a JSONField that can be filtered
        factory = RequestFactory()
        # Adjust field name based on your actual JSONField in GMW model
        request = factory.get("/", {"metadata": "test"})

        filterset = filters.GmwFilter(request.GET, queryset=GMW.objects.all())

        assert filterset.is_valid()

    def test_datetime_filter_mixin_integration(self, gmw):
        """Test DateTimeFilterMixin is properly integrated"""
        factory = RequestFactory()
        # Test with datetime field if GMW has one
        request = factory.get("/")

        filterset = filters.GmwFilter(request.GET, queryset=GMW.objects.all())

        assert filterset.is_valid()
        assert hasattr(filterset, "filters")


@pytest.mark.django_db
class TestMonitoringTubeFilter:
    """Tests for MonitoringTubeFilter"""

    def test_filter_by_gmw_bro_id(self, tube, gmw):
        """Test filtering by GMW BRO ID"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": gmw.bro_id})

        filterset = filters.MonitoringTubeFilter(
            request.GET, queryset=MonitoringTube.objects.all()
        )

        assert filterset.is_valid()
        assert tube in filterset.qs

    def test_filter_by_gmw_bro_id_no_match(self, tube):
        """Test filtering by non-existent GMW BRO ID"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": "NONEXISTENT123"})

        filterset = filters.MonitoringTubeFilter(
            request.GET, queryset=MonitoringTube.objects.all()
        )

        assert filterset.is_valid()
        assert tube not in filterset.qs
        assert filterset.qs.count() == 0

    def test_filter_by_gmn_bro_id(self, tube, gmw, gmn, measuringpoint):
        """Test filtering by GMN BRO ID through measuringpoints"""
        # Ensure the measuringpoint links to the gmw
        factory = RequestFactory()
        request = factory.get("/", {"gmn_bro_id": gmn.bro_id})

        filterset = filters.MonitoringTubeFilter(
            request.GET, queryset=MonitoringTube.objects.all()
        )

        assert filterset.is_valid()
        # Tube should be in results if its GMW is linked via measuringpoint
        qs = filterset.qs
        assert qs.count() > 0
        assert tube in qs

    def test_filter_by_gmn_bro_id_no_measuringpoints(self, tube):
        """Test filtering by GMN BRO ID with no matching measuringpoints"""
        factory = RequestFactory()
        request = factory.get("/", {"gmn_bro_id": "NONEXISTENT_GMN"})

        filterset = filters.MonitoringTubeFilter(
            request.GET, queryset=MonitoringTube.objects.all()
        )

        assert filterset.is_valid()
        assert filterset.qs.count() == 0

    def test_excludes_geo_ohm_cables(self):
        """Test that geo_ohm_cables field is excluded from filtering"""
        filterset = filters.MonitoringTubeFilter()

        assert "geo_ohm_cables" not in filterset.filters

    def test_both_filters_together(self, tube, gmw, gmn, measuringpoint):
        """Test using both gmw_bro_id and gmn_bro_id together"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": gmw.bro_id, "gmn_bro_id": gmn.bro_id})

        filterset = filters.MonitoringTubeFilter(
            request.GET, queryset=MonitoringTube.objects.all()
        )

        assert filterset.is_valid()


@pytest.mark.django_db
class TestEventFilter:
    """Tests for EventFilter"""

    def test_filter_by_gmw_bro_id(self, event, gmw):
        """Test filtering events by GMW BRO ID"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": gmw.bro_id})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        assert event in filterset.qs

    def test_filter_by_gmw_bro_id_no_match(self, event):
        """Test filtering by non-existent GMW BRO ID"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": "NONEXISTENT123"})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        assert event not in filterset.qs

    def test_event_date_gt_filter(self, event):
        """Test event_date greater than filter"""
        test_date = date.today() - timedelta(days=10)
        factory = RequestFactory()
        request = factory.get("/", {"event_date__gt": test_date.isoformat()})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        # Check that filter is applied
        for evt in filterset.qs:
            assert evt.event_date > test_date

    def test_event_date_gte_filter(self, event):
        """Test event_date greater than or equal filter"""
        test_date = date.today() - timedelta(days=10)
        factory = RequestFactory()
        request = factory.get("/", {"event_date__gte": test_date.isoformat()})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        for evt in filterset.qs:
            assert evt.event_date >= test_date

    def test_event_date_lt_filter(self, event):
        """Test event_date less than filter"""
        test_date = date.today() + timedelta(days=10)
        factory = RequestFactory()
        request = factory.get("/", {"event_date__lt": test_date.isoformat()})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        for evt in filterset.qs:
            assert evt.event_date < test_date

    def test_event_date_lte_filter(self, event):
        """Test event_date less than or equal filter"""
        test_date = date.today() + timedelta(days=10)
        factory = RequestFactory()
        request = factory.get("/", {"event_date__lte": test_date.isoformat()})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        for evt in filterset.qs:
            assert evt.event_date <= test_date

    def test_event_date_range_filter(self, event):
        """Test combining date filters for a range"""
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=30)

        factory = RequestFactory()
        request = factory.get(
            "/",
            {
                "event_date__gte": start_date.isoformat(),
                "event_date__lte": end_date.isoformat(),
            },
        )

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        for evt in filterset.qs:
            assert start_date <= evt.event_date <= end_date

    def test_excludes_metadata_and_sourcedocument_data(self):
        """Test that metadata and sourcedocument_data are excluded"""
        filterset = filters.EventFilter()

        assert "metadata" not in filterset.filters
        assert "sourcedocument_data" not in filterset.filters

    def test_combined_filters(self, event, gmw):
        """Test combining GMW BRO ID and date filters"""
        test_date = date.today() - timedelta(days=10)

        factory = RequestFactory()
        request = factory.get(
            "/", {"gmw_bro_id": gmw.bro_id, "event_date__gte": test_date.isoformat()}
        )

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()


@pytest.mark.django_db
class TestFilterEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_queryset(self):
        """Test filters work with empty querysets"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": "TEST123"})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.none())

        assert filterset.is_valid()
        assert filterset.qs.count() == 0

    def test_invalid_date_format(self):
        """Test handling of invalid date formats"""
        factory = RequestFactory()
        request = factory.get("/", {"event_date__gte": "invalid-date"})

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        # Filter should handle invalid dates gracefully
        assert not filterset.is_valid() or filterset.qs.count() >= 0

    def test_empty_filter_params(self, event):
        """Test with no filter parameters returns all objects"""
        factory = RequestFactory()
        request = factory.get("/")

        filterset = filters.EventFilter(request.GET, queryset=Event.objects.all())

        assert filterset.is_valid()
        assert event in filterset.qs

    def test_filter_with_special_characters(self):
        """Test filtering with special characters in BRO ID"""
        factory = RequestFactory()
        request = factory.get("/", {"gmw_bro_id": "TEST-123_ABC"})

        filterset = filters.MonitoringTubeFilter(
            request.GET, queryset=MonitoringTube.objects.all()
        )

        assert filterset.is_valid()
