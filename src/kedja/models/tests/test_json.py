from datetime import datetime
from unittest import TestCase

from pyramid import testing
from pyramid.renderers import render
from pytz import UTC


fixture_data = {
    'hello_date': datetime(1970, 1, 1, 12, 00, tzinfo=UTC)
}


class JSONAdapterTests(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('kedja.models.json')

    def tearDown(self):
        testing.tearDown()

    def test_render_json(self):
        self.assertEqual('{"hello_date": "1970-01-01T12:00:00+00:00"}', render('json', fixture_data))
