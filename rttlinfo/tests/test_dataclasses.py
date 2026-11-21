# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

from django.test import SimpleTestCase

from rttlinfo.dataclasses import (
    CourseConfiguration,
    CourseStatus,
    CourseStatusUpdate,
    GitpullerTarget,
    parse_api_datetime,
    serialize_for_api,
)


class ParseApiDatetimeTest(SimpleTestCase):
    def test_empty(self):
        self.assertIsNone(parse_api_datetime(None))
        self.assertIsNone(parse_api_datetime(''))

    def test_zulu_suffix(self):
        self.assertEqual(
            parse_api_datetime('2025-06-03T15:43:40Z'),
            datetime(2025, 6, 3, 15, 43, 40, tzinfo=UTC))

    def test_offset(self):
        parsed = parse_api_datetime('2025-06-03T15:43:40.567793-07:00')
        self.assertEqual(parsed.utcoffset().total_seconds(), -7 * 3600)

    def test_datetime_passthrough(self):
        now = datetime.now()
        self.assertIs(parse_api_datetime(now), now)


class CourseConfigurationTest(SimpleTestCase):
    API_DATA: ClassVar[dict] = {
        'configuration_applied': True,
        'cpu_request': 2,
        'memory_request': 4,
        'storage_request': 5,
        'image_uri': 'https://example.com/image',
        'image_tag': 'main',
        'features_request': 'nfs, binderhub',
        'gitpuller_targets': [{
            'gitpuller_uri': 'https://github.com/o/r.git',
            'gitpuller_tag': 'main',
            'gitpuller_sync_dir': 'materials',
        }],
        'configuration_comments': 'hi',
        'create_timestamp': '2025-06-03T15:43:40.567793-07:00',
    }

    def test_round_trip(self):
        config = CourseConfiguration.from_api_data(self.API_DATA)
        self.assertIsInstance(config.gitpuller_targets[0], GitpullerTarget)
        self.assertIsNotNone(config.create_timestamp)
        expected = dict(self.API_DATA)
        del expected['create_timestamp']
        self.assertEqual(config.to_api_data(), expected)

    def test_defaults_when_sparse(self):
        config = CourseConfiguration.from_api_data({})
        self.assertFalse(config.configuration_applied)
        self.assertEqual(config.gitpuller_targets, [])
        self.assertIsNone(config.create_timestamp)

    def test_features_list(self):
        config = CourseConfiguration()
        self.assertEqual(config.get_features_list(), [])
        config.set_features_list(['nfs', 'binderhub'])
        self.assertEqual(config.features_request, 'nfs, binderhub')
        self.assertEqual(config.get_features_list(), ['nfs', 'binderhub'])


class CourseStatusTest(SimpleTestCase):
    def test_display(self):
        self.assertEqual(
            CourseStatus(id=1, status='deployed').get_status_display(),
            'Deployed')
        self.assertEqual(
            CourseStatus(id=1, status='weird').get_status_display(), 'weird')

    def test_invalid_email_rejected(self):
        with self.assertRaises(ValueError):
            CourseStatus(id=1, status='requested', status_added_by='nope')
        CourseStatus(id=1, status='requested', status_added_by='a@uw.edu')


class CourseStatusUpdateTest(SimpleTestCase):
    def test_configuration_only_included_when_set(self):
        update = CourseStatusUpdate(sis_course_id='x', status='requested')
        self.assertNotIn('configuration', update.to_api_data())
        update.configuration = CourseConfiguration(cpu_request=2)
        self.assertEqual(
            update.to_api_data()['configuration']['cpu_request'], 2)

    def test_hub_admins(self):
        update = CourseStatusUpdate(
            sis_course_id='x', status='requested', hub_admins=['a'])
        self.assertEqual(update.to_api_data()['hub_admins'], ['a'])


class SerializeForApiTest(SimpleTestCase):
    def test_prefers_to_api_data(self):
        target = GitpullerTarget('u', 't', 'd')
        self.assertEqual(serialize_for_api(target), target.to_api_data())

    def test_generic_dataclass(self):
        @dataclass
        class Inner:
            when: datetime

        @dataclass
        class Outer:
            inner: Inner
            items: list
            name: str

        when = datetime(2025, 1, 2, 3, 4, 5)
        result = serialize_for_api(Outer(Inner(when), [Inner(when), 1], 'n'))
        iso = when.isoformat()
        self.assertEqual(result, {
            'inner': {'when': iso},
            'items': [{'when': iso}, 1],
            'name': 'n',
        })
