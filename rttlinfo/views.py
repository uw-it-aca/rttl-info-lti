# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.http import HttpResponse
from django.views.generic import TemplateView
from blti.views import BLTILaunchView
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from logging import getLogger
from .api.repositories.rttl_repository import RttlInfoRepository
from django.shortcuts import render, redirect
from .forms import CourseConfigurationForm
from .api.clients.rttl_client import get_rttl_client, RttlApiError
from .dataclasses import CourseStatusUpdate
from .utils import get_course_eligibility
logger = getLogger(__name__)


class LaunchView(BLTILaunchView):
    template_name = 'rttlinfo/home.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rttl_repository = RttlInfoRepository()

    def dispatch(self, request, *args, **kwargs):
        logger.debug(f"Launching LTI with request: {request}")
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        request.is_secure = lambda: True
        # DEV __ONLY__ ^^
        response = super().dispatch(request, *args, **kwargs)
        request.session['blti_data'] = {
            'canvas_course_id': self.blti.canvas_course_id,
            'course_sis_id': self.blti.course_sis_id,
            'course_name': self.blti.course_short_name,
            'course_short_name': self.blti.course_short_name,
            'course_long_name': self.blti.course_long_name,
            'is_instructor': self.blti.is_instructor,
            'is_ta': self.blti.is_teaching_assistant,
            'is_student': self.blti.is_student,
            'is_admin': self.blti.is_administrator,
            'user_email': self.blti.user_email,
            'is_eligible': get_course_eligibility(self.blti.course_sis_id),
        }

        return response

    def get_context_data(self, **kwargs):
        _ = super().get_context_data(**kwargs)
        # Return basic context without API call
        # hub data will be loaded via AJAX
        return {
            'session_id': self.request.session.session_key,
            'canvas_course_id': self.blti.canvas_course_id,
            'course_sis_id': self.blti.course_sis_id,
            'course_name': self.blti.course_short_name,
            'course_long_name': self.blti.course_long_name,
            'is_instructor': self.blti.is_instructor,
            'is_ta': self.blti.is_teaching_assistant,
            'is_student': self.blti.is_student,
            'is_admin': self.blti.is_administrator,
            'is_eligible': get_course_eligibility(self.blti.course_sis_id),
            'load_hub_data_async': True,  # Flag to trigger AJAX loading
        }


class HubDataApiView(TemplateView):
    """
    API endpoint for loading hub data asynchronously.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rttl_repository = RttlInfoRepository()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        course_sis_id = request.GET.get('course_sis_id')

        if course_sis_id in [None, 'None', '']:
            return JsonResponse(
                {'error': 'course_sis_id parameter required'}, status=400)

        try:
            # Fetch rttl api data using repository
            rttl_data = self.rttl_repository.get_course_status(course_sis_id)
            """
            Returns something like:
            [{'id': 11, 'name': 'PSYCH 102 A Au 19, Introduction To Psychology II', 'course_year': 2019, 'course_quarter': 4, 'sis_course_id': '2019-autumn-PSYCH-102-A', 'hub_url': '', 'last_changed': '2025-06-03T15:43:40.363412-07:00', 'latest_status': {'id': 16, 'status': 'requested', 'hub_deployed': False, 'message': 'JupyterHub configuration requested via web form', 'configuration': {'configuration_applied': False, 'cpu_request': 2, 'memory_request': 3, 'storage_request': 4, 'image_uri': 'https://example.com/imagename', 'image_tag': 'main', 'features_request': '', 'gitpuller_targets': [], 'configuration_comments': 'heyhey', 'create_timestamp': '2025-06-03T15:43:40.567793-07:00'}, 'status_added': '2025-06-03T15:43:40.565744-07:00', 'course': 11}, 'in_admin_courses': False}]
            """
            rttl_hub_exists = False
            rttl_hub_url = None
            rttl_hub_deployed = False
            rttl_hub_status = None
            rttl_hub_status_message = None

            if rttl_data:
                rttl_hub_exists = True
                rttl_hub_url = rttl_data[0].get('hub_url')
                rttl_hub_deployed = True if rttl_hub_url else False
                rttl_hub_status = rttl_data[0]['latest_status'].get('status')
                rttl_hub_status_message = rttl_data[0]['latest_status'].get(
                    'message')

            return JsonResponse({
                'rttl_hub_exists': rttl_hub_exists,
                'rttl_hub_url': rttl_hub_url,
                'rttl_hub_deployed': rttl_hub_deployed,
                'rttl_hub_status': rttl_hub_status,
                'rttl_hub_status_message': rttl_hub_status_message,
            })

        except Exception as e:
            logger.error(f"Error fetching hub data: {e}")
            return JsonResponse({'error': 'Failed to fetch hub data'},
                                status=500)


class HubManageView(TemplateView):
    template_name = 'rttlinfo/manage.html'
    cache_time = 60 * 60 * 4
    date_format = '%a, %d %b %Y %H:%M:%S GMT'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rttl_repository = RttlInfoRepository()

    def get_context_data(self, **kwargs):
        _ = super().get_context_data(**kwargs)
        querystring = self.request.environ.get('QUERY_STRING')
        q_list = querystring.split('&')
        course_sis_id = None
        for q in q_list:
            q_split = q.split('=')
            if q_split[0] == 'course_sis_id':
                course_sis_id = q_split[1]
                break
        if not course_sis_id:
            return HttpResponse(status=400, content='Missing course_sis_id')
        rttl_data = self.rttl_repository.get_course_status(course_sis_id)
        """
        Returns something like:
        {'id': 11, 'name': 'PSYCH 102 A Au 19, Introduction To Psychology II', 'course_year': 2019, 'course_quarter': 4, 'sis_course_id': '2019-autumn-PSYCH-102-A', 'hub_url': '', 'last_changed': '2025-06-03T15:43:40.363412-07:00', 'statuses': [{'id': 16, 'status': 'requested', 'hub_deployed': False, 'message': 'JupyterHub configuration requested via web form', 'configuration': {'configuration_applied': False, 'cpu_request': 2, 'memory_request': 3, 'storage_request': 4, 'image_uri': 'https://example.com/imagename', 'image_tag': 'main', 'features_request': '', 'gitpuller_targets': [], 'configuration_comments': 'heyhey', 'create_timestamp': '2025-06-03T15:43:40.567793-07:00'}, 'status_added': '2025-06-03T15:43:40.565744-07:00', 'course': 11}], 'in_admin_courses': False}
        """
        if not rttl_data:
            # Must be a new hub request
            pass


class HubRequestView(TemplateView):
    template_name = 'rttlinfo/request.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blti_data'] = self.request.session.get('blti_data', {})
        context['form'] = CourseConfigurationForm()
        # Alt for a full hub request with course info:
        # context['form'] = HubRequestForm()

        return context

    def post(self, request, *args, **kwargs):
        form = CourseConfigurationForm(request.POST)
        if form.is_valid():
            try:
                # Get BLTI data from session
                blti_data = request.session.get('blti_data', {})
                sis_course_id = blti_data.get('course_sis_id')

                if not sis_course_id:
                    messages.error(request, 'Unable to identify course. \
                    Please try launching from Canvas again.')
                    return render(request, self.template_name, {'form': form})

                # Convert form to dataclass
                config_dataclass = form.to_dataclass()
                # create_timestamp=None
                logger.info(f"Created configuration dataclass: \
                            {config_dataclass}")

                # Create the status update payload
                status_update = CourseStatusUpdate(
                    sis_course_id=sis_course_id,
                    status='requested',
                    auto_create=True,
                    hub_deployed=False,
                    message=f"JupyterHub configuration requested via web form. Email <a href='mailto:help@uw.edu?subject={sis_course_id}'>help@uw.edu</a> if you need to make changes.",
                    configuration=config_dataclass,
                    # Populate course info from BLTI data if available
                    name=blti_data.get('course_long_name', '')
                )

                # Use RttlApiClient to submit the request
                client = get_rttl_client()
                response = client.create_or_update_course_status(
                    status_update.to_api_data())

                logger.info(f"API response: {response}")

                # Success message
                messages.success(
                    request,
                    'Your JupyterHub request has been submitted successfully! '
                    'You will receive an email notification when '
                    'your hub is ready.'
                )
                return render(request, 'rttlinfo/home.html', blti_data)

            except RttlApiError as e:
                logger.error(f"API error when creating course status: {e}")
                if e.status_code == 404:
                    messages.error(request,
                                   'Course not found. Please contact support.')
                elif e.status_code == 400:
                    messages.error(request,
                                   f'Invalid request: {e.message}')
                else:
                    messages.error(request,
                                   'An error occurred while submitting your '
                                   'request. Please try again.')

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                messages.error(request,
                               'An unexpected error occurred. Please try '
                               'again or contact support.')

        # If form is invalid or there was an error, re-render with form errors
        return render(request, self.template_name, {'form': form})


class HubStatusApiView(TemplateView):
    """
    API endpoint for checking hub status.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        sis_course_id = request.GET.get('sis_course_id')

        if sis_course_id in [None, 'None', '']:
            return JsonResponse(
                {'error': 'sis_course_id parameter required'}, status=400)

        try:
            client = get_rttl_client()
            course_data = client.get_course_by_sis_id(sis_course_id)

            if not course_data:
                return JsonResponse({'error': 'Course not found'}, status=404)

            # Get the latest status
            latest_status = course_data.get('latest_status')
            if latest_status:
                return JsonResponse({
                    'status': latest_status['status'],
                    'hub_deployed': latest_status.get('hub_deployed', False),
                    'message': latest_status.get('message', ''),
                    'hub_url': course_data.get('hub_url', ''),
                    'last_updated': latest_status.get('status_added')
                })
            else:
                return JsonResponse({
                    'status': 'unknown',
                    'message': 'No status information available'
                })

        except RttlApiError as e:
            logger.error(f"API error: {e}")
            return JsonResponse({'error': 'API error occurred'}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


# Helper view for updating existing configurations
# Check if needed
class HubUpdateConfigView(TemplateView):
    template_name = 'rttlinfo/update_config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        blti_data = self.request.session.get('blti_data', {})
        sis_course_id = blti_data.get('lis_course_offering_sourcedid')

        if sis_course_id:
            try:
                client = get_rttl_client()
                course_data = client.get_course_by_sis_id(sis_course_id)

                if course_data:
                    # Get the applied configuration
                    configs = client.list_course_configs(
                        course_data['id'],
                        applied=True)
                    if configs:
                        # Pre-populate form with existing configuration
                        form = CourseConfigurationForm()
                        # Use the applied config
                        form.from_dataclass(configs[0])
                        context['form'] = form
                        context['existing_config'] = configs[0]
                    else:
                        context['form'] = CourseConfigurationForm()

                    context['course'] = course_data
                else:
                    context['error'] = 'Course not found'

            except RttlApiError as e:
                logger.error(f"Error fetching course data: {e}")
                context['error'] = "Unable to fetch course information"

        if 'form' not in context:
            context['form'] = CourseConfigurationForm()

        return context

    def post(self, request, *args, **kwargs):
        form = CourseConfigurationForm(request.POST)

        if form.is_valid():
            try:
                blti_data = request.session.get('blti_data', {})
                sis_course_id = blti_data.get('lis_course_offering_sourcedid')

                if not sis_course_id:
                    messages.error(request, 'Unable to identify course.')
                    return render(request, self.template_name, {'form': form})

                # Convert form to dataclass
                config_dataclass = form.to_dataclass()

                # Create a new status with updated configuration
                status_update = CourseStatusUpdate(
                    sis_course_id=sis_course_id,
                    status='requested',  # Status for configuration update
                    auto_create=False,   # Course should already exist
                    hub_deployed=False,
                    message='Configuration updated via web form',
                    configuration=config_dataclass
                )

                # Submit the update
                client = get_rttl_client()
                _ = client.create_or_update_course_status(
                    status_update.to_api_data())

                messages.success(
                    request,
                    'Configuration updated successfully!')
                return redirect('hub-manage')

            except RttlApiError as e:
                logger.error(f"API error: {e}")
                messages.error(
                    request,
                    f'Error updating configuration: {e.message}')
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                messages.error(request, 'An unexpected error occurred.')

        return render(request, self.template_name, {'form': form})
