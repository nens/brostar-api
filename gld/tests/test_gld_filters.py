from django.test import TestCase

from api.models import Organisation
from gld.filters import GldFilter
from gld.models import GLD


class GldFilterTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Organisation")
        self.gld1 = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000001234"
        )
        self.gld2 = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000080137"
        )

    def test_gld_filter(self):
        filter_set = GldFilter({"bro_id": "GLD0000001234"}, queryset=GLD.objects.all())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first().bro_id, "GLD0000001234")
