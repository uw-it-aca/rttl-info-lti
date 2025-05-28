# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

# from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse
from django.views.generic import TemplateView, View
from blti.views import BLTILaunchView  #, RESTDispatch
# from restclients_core.exceptions import DataFailureException
# from rttlinfo.dao.canvas import (
#     get_users_for_course, get_viewable_sections)
# from datetime import datetime, timedelta, timezone
# from urllib.parse import urlparse, parse_qs
from logging import getLogger
from .api.repositories.rttl_repository import RttlInfoRepository

logger = getLogger(__name__)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class LaunchView(BLTILaunchView):
    template_name = 'rttlinfo/home.html'
    authorized_role = 'admin'
    # TODO: investigate ^^

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rttl_repository = RttlInfoRepository()

    def dispatch(self, request, *args, **kwargs):
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        # DEV __ONLY__ ^^ Used because django runserver doesn't handle this correctly
        # import pdb; pdb.set_trace()  # Breakpoint before any auth checks
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # TODO: Fetch rttl api data using repository
        rttl_data = self.rttl_repository.get_course_status(
            self.blti.course_sis_id)
        # import pdb; pdb.set_trace()  # Breakpoint to inspect rttl_data
        if rttl_data:
            rttl_hub_exists = True
            rttl_hub_url = rttl_data[0].get('hub_url')
            rttl_hub_deployed = True if rttl_hub_url else False
            rttl_hub_status = rttl_data[0]['latest_status'].get('status')
            rttl_hub_status_message = rttl_data[0]['latest_status'].get('message')

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
            'rttl_hub_exists': rttl_hub_exists,
            'rttl_hub_url': rttl_hub_url,
            'rttl_hub_deployed': rttl_hub_deployed,
            'rttl_hub_status': rttl_hub_status,
            'rttl_hub_status_message': rttl_hub_status_message,
        }


class HubDetailsView(TemplateView):
    template_name = 'rttlinfo/details.html'
    cache_time = 60 * 60 * 4
    date_format = '%a, %d %b %Y %H:%M:%S GMT'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rttl_repository = RttlInfoRepository()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # import pdb; pdb.set_trace()  # Breakpoint to inspect context
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
        if not rttl_data:
            # Must be a new hub request
            pass        
