# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

import requests
from django.core.cache import cache
from django.test import SimpleTestCase

from rttlinfo.api.clients.rttl_client import (
    RttlApiClient,
    RttlApiError,
    get_rttl_client,
)


def make_response(status=200, data=None, text=''):
    response = mock.Mock(spec=requests.Response)
    response.status_code = status
    response.text = text
    response.content = b'x' if data is not None else b''
    if data is None:
        response.json.side_effect = ValueError('no json')
    else:
        response.json.return_value = data
    if status >= 400:
        error = requests.exceptions.HTTPError(response=response)
        response.raise_for_status.side_effect = error
    return response


class RttlApiClientTest(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.client = RttlApiClient(
            base_url='https://rttl.example.edu', api_key='key')
        self.request = mock.patch.object(self.client.session, 'request')
        self.request = self.request.start()
        self.addCleanup(mock.patch.stopall)

    def test_requires_api_key(self):
        with self.settings(RTTL_API_KEY=''), self.assertRaises(ValueError):
            RttlApiClient(base_url='https://x')

    def test_defaults_from_settings(self):
        client = RttlApiClient()
        self.assertEqual(client.base_url, 'https://rttl.example.edu')
        self.assertEqual(
            client.session.headers['Authorization'],
            'Bearer Api-Key test-api-key')

    def test_get_rttl_client_cache_toggle(self):
        self.assertEqual(get_rttl_client(use_cache=False).cache_timeout, 0)
        self.assertEqual(get_rttl_client().cache_timeout, 300)

    def test_url_building(self):
        self.assertEqual(
            self.client._get_url('/courses/'),
            'https://rttl.example.edu/api/v1/courses/')

    def test_cache_key_is_safe_and_param_sensitive(self):
        key_a = self.client._get_cache_key('GET', 'courses/', {'sis_id': 'a b&'})
        key_b = self.client._get_cache_key('GET', 'courses/', {'sis_id': 'c'})
        self.assertRegex(key_a, r'^rttl_api_[0-9a-f]{32}$')
        self.assertNotEqual(key_a, key_b)

    def test_list_courses_passes_sis_filter(self):
        self.request.return_value = make_response(data=[{'id': 1}])
        self.assertEqual(self.client.list_courses('2024-autumn-X-1-A'),
                         [{'id': 1}])
        args, kwargs = self.request.call_args
        self.assertEqual(args, ('GET', 'https://rttl.example.edu/api/v1/courses/'))
        self.assertEqual(kwargs['params'], {'sis_id': '2024-autumn-X-1-A'})

    def test_get_requests_are_cached(self):
        self.request.return_value = make_response(data=[{'id': 1}])
        self.client.list_courses()
        self.assertEqual(self.client.list_courses(), [{'id': 1}])
        self.assertEqual(self.request.call_count, 1)

    def test_use_cache_false_bypasses_cache(self):
        self.request.return_value = make_response(data=[{'id': 1}])
        self.client.list_courses(use_cache=False)
        self.client.list_courses(use_cache=False)
        self.assertEqual(self.request.call_count, 2)

    def test_post_sends_json_and_is_not_cached(self):
        self.request.return_value = make_response(201, {'ok': True})
        payload = {'sis_course_id': 'x'}
        self.assertEqual(
            self.client.create_or_update_course_status(payload), {'ok': True})
        self.assertEqual(self.request.call_args.kwargs['json'], payload)
        self.client.create_or_update_course_status(payload)
        self.assertEqual(self.request.call_count, 2)

    def test_http_error_raises_api_error_with_details(self):
        self.request.return_value = make_response(404, {'detail': 'nope'})
        with self.assertRaises(RttlApiError) as ctx:
            self.client.get_course(99)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.response_data, {'detail': 'nope'})

    def test_http_error_with_non_json_body(self):
        self.request.return_value = make_response(500)
        with self.assertRaises(RttlApiError) as ctx:
            self.client.get_course(99)
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIsNone(ctx.exception.response_data)

    def test_connection_error(self):
        self.request.side_effect = requests.exceptions.ConnectionError('down')
        with self.assertRaises(RttlApiError) as ctx:
            self.client.get_course(1)
        self.assertIsNone(ctx.exception.status_code)

    def test_invalid_json_in_success_response(self):
        self.request.return_value = make_response(200, None)
        with self.assertRaises(RttlApiError):
            self.client.get_course(1, use_cache=False)

    def test_get_course_by_sis_id(self):
        self.request.return_value = make_response(data=[{'id': 3}, {'id': 4}])
        self.assertEqual(self.client.get_course_by_sis_id('x'), {'id': 3})
        self.request.return_value = make_response(data=[])
        self.assertIsNone(
            self.client.get_course_by_sis_id('y', use_cache=False))
