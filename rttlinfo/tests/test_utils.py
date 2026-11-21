# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase

from rttlinfo import utils


class GetTermFromStringTest(SimpleTestCase):
    def test_numeric_terms(self):
        self.assertEqual(utils.get_term_from_string('1'), 1)
        self.assertEqual(utils.get_term_from_string('4'), 4)

    def test_numeric_out_of_range(self):
        for value in ('0', '5'):
            with self.assertRaises(utils.InvalidTermError):
                utils.get_term_from_string(value)

    def test_names_and_abbreviations(self):
        cases = {
            'Winter': 1, 'wi': 1, 'SPRING': 2, 'sp': 2,
            'summer': 3, 'su': 3, 'autumn': 4, 'aut': 4,
        }
        for value, expected in cases.items():
            self.assertEqual(utils.get_term_from_string(value), expected)

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            utils.get_term_from_string('fall')


class ValidateSourceSisTest(SimpleTestCase):
    def test_valid(self):
        sis_id = '2024-autumn-CSE-142-A'
        source, match = utils.validate_source_sis(sis_id)
        self.assertEqual(source, sis_id)
        self.assertEqual(match.groups()[:3], ('2024', 'autumn', 'CSE'))

    def test_curriculum_with_ampersand_and_space(self):
        _, match = utils.validate_source_sis('2024-winter-B H&P-101-AA')
        self.assertEqual(match.group(3), 'B H&P')

    def test_empty(self):
        for value in (None, ''):
            with self.assertRaises(ValueError):
                utils.validate_source_sis(value)

    def test_bad_format(self):
        with self.assertRaises(ValueError):
            utils.validate_source_sis('not-a-sis-id')


class GetCourseEligibilityTest(SimpleTestCase):
    def setUp(self):
        self.sws = mock.patch.object(
            utils, 'get_term_from_sws',
            return_value={'year': 2025, 'quarter': 'Spring'})
        self.sws.start()
        self.addCleanup(self.sws.stop)

    def test_invalid_sis_not_eligible(self):
        self.assertFalse(utils.get_course_eligibility('bogus'))
        self.assertFalse(utils.get_course_eligibility(None))

    def test_future_year_skips_sws(self):
        self.assertTrue(utils.get_course_eligibility('2999-autumn-CSE-142-A'))
        utils.get_term_from_sws.assert_not_called()

    def test_past_year(self):
        self.assertFalse(utils.get_course_eligibility('2020-autumn-CSE-142-A'))

    def test_current_year_earlier_term(self):
        self.assertFalse(utils.get_course_eligibility('2025-winter-CSE-142-A'))

    def test_current_year_same_or_later_term(self):
        self.assertTrue(utils.get_course_eligibility('2025-spring-CSE-142-A'))
        self.assertTrue(utils.get_course_eligibility('2025-autumn-CSE-142-A'))


class GetTermFromSwsTest(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_fetches_and_caches(self):
        term = mock.Mock()
        term.json_data.return_value = {'year': 2025, 'quarter': 'Spring'}
        with mock.patch.object(
                utils.sws_term, 'get_current_term',
                return_value=term) as get_term:
            first = utils.get_term_from_sws()
            second = utils.get_term_from_sws()
        self.assertEqual(first, {'year': 2025, 'quarter': 'Spring'})
        self.assertEqual(second, first)
        get_term.assert_called_once()

    def test_use_cache_false_always_fetches(self):
        term = mock.Mock()
        term.json_data.return_value = {'year': 2025, 'quarter': 'Spring'}
        with mock.patch.object(
                utils.sws_term, 'get_current_term',
                return_value=term) as get_term:
            utils.get_term_from_sws(use_cache=False)
            utils.get_term_from_sws(use_cache=False)
        self.assertEqual(get_term.call_count, 2)
