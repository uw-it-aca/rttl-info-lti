# Copyright 2026 UWIT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import json
from unittest import mock

from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rttlinfo.api.clients.rttl_client import RttlApiError
from rttlinfo.views import HubStatusApiView, LaunchView

BLTI_DATA = {
    'canvas_course_id': '123',
    'course_sis_id': '2024-autumn-CSE-142-A',
    'course_short_name': 'CSE 142',
    'course_long_name': 'CSE 142 A Au 24, Intro',
    'is_instructor': True,
    'user_email': 'prof@uw.edu',
    'user_full_name': 'Pat Prof',
}

FORM_DATA = {
    'cpu_request': '2',
    'memory_request': '4',
    'storage_request': '5',
    'container_image': 'scipy',
}


def set_session(client, **data):
    session = client.session
    session.update(data)
    session.save()


class HubDataApiViewTest(TestCase):
    def setUp(self):
        patcher = mock.patch('rttlinfo.views.RttlInfoRepository')
        self.repo = patcher.start().return_value
        self.addCleanup(patcher.stop)
        self.url = reverse('hub-data-api')

    def get(self, sis_id='2024-autumn-CSE-142-A'):
        return self.client.get(self.url, {'course_sis_id': sis_id})

    def test_missing_param(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_existing_hub(self):
        self.repo.get_course_status.return_value = [{
            'hub_url': 'https://hub.example.edu',
            'hub_admins': ['a'],
            'latest_status': {
                'status': 'deployed', 'hub_deployed': True, 'message': 'ok'},
        }]
        data = self.get().json()
        self.assertTrue(data['rttl_hub_exists'])
        self.assertTrue(data['rttl_hub_deployed'])
        self.assertEqual(data['rttl_hub_status'], 'deployed')
        self.assertEqual(data['rttl_hub_admins'], ['a'])
        self.assertFalse(data['is_eligible'])

    def test_course_without_latest_status_is_error(self):
        self.repo.get_course_status.return_value = [{'hub_url': ''}]
        self.assertEqual(self.get().status_code, 500)

    def test_no_hub_reports_eligibility(self):
        self.repo.get_course_status.return_value = []
        with mock.patch('rttlinfo.views.get_course_eligibility',
                        return_value=True) as eligibility:
            data = self.get().json()
        eligibility.assert_called_once_with('2024-autumn-CSE-142-A')
        self.assertFalse(data['rttl_hub_exists'])
        self.assertTrue(data['is_eligible'])

    def test_eligibility_failure_is_not_fatal(self):
        self.repo.get_course_status.return_value = []
        with mock.patch('rttlinfo.views.get_course_eligibility',
                        side_effect=RuntimeError('sws down')):
            response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_eligible'])

    def test_repository_failure(self):
        self.repo.get_course_status.side_effect = RttlApiError('boom')
        self.assertEqual(self.get().status_code, 500)


class HomeViewTest(TestCase):
    def test_uses_session_data(self):
        set_session(self.client, blti_data=BLTI_DATA)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['course_sis_id'], BLTI_DATA['course_sis_id'])
        self.assertTrue(response.context['is_instructor'])
        self.assertFalse(response.context['is_admin'])

    def test_without_session_data(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['course_sis_id'], '')


class HubRequestViewTest(TestCase):
    def setUp(self):
        self.url = reverse('hub-request')
        patcher = mock.patch('rttlinfo.views.get_rttl_client')
        self.get_client = patcher.start()
        self.api = self.get_client.return_value
        self.api.create_or_update_course_status.return_value = {'ok': True}
        self.addCleanup(patcher.stop)

    def messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_get_renders_form(self):
        set_session(self.client, blti_data=BLTI_DATA)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['blti_data'], BLTI_DATA)
        self.assertIn('form', response.context)

    def test_post_success_submits_status_and_redirects(self):
        set_session(self.client, blti_data=BLTI_DATA)
        response = self.client.post(
            self.url, dict(FORM_DATA, additional_admins='ta@uw.edu, other'))
        self.assertRedirects(
            response, reverse('home'), fetch_redirect_response=False)
        payload = self.api.create_or_update_course_status.call_args.args[0]
        self.assertEqual(payload['sis_course_id'], BLTI_DATA['course_sis_id'])
        self.assertEqual(payload['status'], 'requested')
        self.assertTrue(payload['auto_create'])
        self.assertEqual(payload['status_added_by'], 'prof@uw.edu')
        self.assertEqual(payload['hub_admins'], ['ta', 'other', 'prof'])
        self.assertEqual(payload['configuration']['cpu_request'], 2)

    def test_post_without_course_in_session(self):
        response = self.client.post(self.url, FORM_DATA)
        self.assertEqual(response.status_code, 200)
        self.api.create_or_update_course_status.assert_not_called()
        self.assertIn('Unable to identify course', self.messages(response)[0])

    def test_post_invalid_form_rerenders(self):
        set_session(self.client, blti_data=BLTI_DATA)
        response = self.client.post(
            self.url, dict(FORM_DATA, cpu_request='64'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.api.create_or_update_course_status.assert_not_called()

    def test_post_api_errors_map_to_messages(self):
        set_session(self.client, blti_data=BLTI_DATA)
        cases = {
            404: 'Course not found',
            400: 'Invalid request: bad',
            500: 'An error occurred while submitting',
        }
        for status, expected in cases.items():
            self.api.create_or_update_course_status.side_effect = \
                RttlApiError('bad', status)
            response = self.client.post(self.url, FORM_DATA)
            self.assertEqual(response.status_code, 200)
            self.assertIn(expected, self.messages(response)[-1])

    def test_post_unexpected_error(self):
        set_session(self.client, blti_data=BLTI_DATA)
        self.api.create_or_update_course_status.side_effect = RuntimeError()
        response = self.client.post(self.url, FORM_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertIn('unexpected error', self.messages(response)[-1])


class HubStatusApiViewTest(TestCase):
    def get(self, query='sis_course_id=x'):
        request = RequestFactory().get('/status/?' + query)
        return HubStatusApiView.as_view()(request)

    def run_with_client(self, **config):
        with mock.patch('rttlinfo.views.get_rttl_client') as get_client:
            get_client.return_value.get_course_by_sis_id.configure_mock(
                **config)
            return self.get()

    def test_missing_param(self):
        self.assertEqual(self.get('').status_code, 400)

    def test_not_found(self):
        self.assertEqual(self.run_with_client(return_value=None).status_code,
                         404)

    def test_with_status(self):
        response = self.run_with_client(return_value={
            'hub_url': 'https://hub',
            'latest_status': {'status': 'deployed', 'hub_deployed': True},
        })
        body = json.loads(response.content)
        self.assertEqual(body['status'], 'deployed')
        self.assertEqual(body['hub_url'], 'https://hub')

    def test_without_status(self):
        response = self.run_with_client(return_value={'hub_url': ''})
        self.assertEqual(json.loads(response.content)['status'], 'unknown')

    def test_api_error(self):
        response = self.run_with_client(side_effect=RttlApiError('x'))
        self.assertEqual(response.status_code, 500)


class LaunchViewTest(TestCase):
    def make_view(self):
        view = LaunchView()
        view.blti = mock.Mock(
            canvas_course_id='1', course_sis_id='sis',
            course_short_name='short', course_long_name='long',
            is_instructor=True, is_teaching_assistant=False,
            is_student=False, is_administrator=False,
            user_email='a@uw.edu', user_full_name='A')
        return view

    def test_blti_data_maps_launch_attributes(self):
        data = self.make_view().blti_data()
        self.assertEqual(data['course_sis_id'], 'sis')
        self.assertTrue(data['is_instructor'])
        self.assertFalse(data['is_ta'])
        self.assertEqual(data['course_name'], 'short')

    def test_dispatch_stores_session_only_for_validated_launch(self):
        def dispatch(view):
            request = RequestFactory().post('/rttlinfo/')
            request.session = {}
            with mock.patch(
                    'blti.views.BLTILaunchView.dispatch',
                    return_value=HttpResponse()):
                view.dispatch(request)
            return request.session

        self.assertEqual(
            dispatch(self.make_view())['blti_data']['course_sis_id'], 'sis')
        self.assertEqual(dispatch(LaunchView()), {})
