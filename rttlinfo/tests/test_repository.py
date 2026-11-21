# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase

from rttlinfo.api.repositories.rttl_repository import RttlInfoRepository


class RttlInfoRepositoryTest(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.client_mock = mock.Mock()
        self.repo = RttlInfoRepository(api_client=self.client_mock)

    def test_invalid_ids(self):
        for method in (self.repo.get_course_status,
                       self.repo.get_course_details,
                       self.repo.get_course_configs):
            for value in (None, '', 'None', 'none'):
                with self.assertRaises(ValueError):
                    method(value)

    def test_status_decodes_id_and_caches(self):
        self.client_mock.list_courses.return_value = [{'id': 1}]
        sis_id = '2024-autumn-B+H%26P-101-A'
        self.assertEqual(self.repo.get_course_status(sis_id), [{'id': 1}])
        self.assertEqual(self.repo.get_course_status(sis_id), [{'id': 1}])
        self.client_mock.list_courses.assert_called_once_with(
            '2024-autumn-B H&P-101-A')

    def test_status_decodes_html_entities(self):
        self.client_mock.list_courses.return_value = []
        self.repo.get_course_status('2024-autumn-B&amp;H-101-A')
        self.client_mock.list_courses.assert_called_once_with(
            '2024-autumn-B&H-101-A')

    def test_details_uses_status_id(self):
        self.client_mock.list_courses.return_value = [{'id': 7}]
        self.client_mock.get_course.return_value = {'id': 7, 'name': 'x'}
        self.assertEqual(
            self.repo.get_course_details('2024-autumn-CSE-142-A'),
            {'id': 7, 'name': 'x'})
        self.client_mock.get_course.assert_called_once_with(7)

    def test_configs_uses_status_id(self):
        self.client_mock.list_courses.return_value = [{'id': 7}]
        self.client_mock.list_course_configs.return_value = [{'cpu': 2}]
        self.assertEqual(
            self.repo.get_course_configs('2024-autumn-CSE-142-A'),
            [{'cpu': 2}])
        self.client_mock.list_course_configs.assert_called_once_with(7)
