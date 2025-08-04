# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache

from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt
from .views import \
    LaunchView, \
    HubDataApiView, \
    HubRequestView, \
    HubManageView

urlpatterns = [
    # LTI launch throws CSRF errors since it's a POST from external domain
    re_path(r'^$', csrf_exempt(LaunchView.as_view()), name='lti-launch'),
    re_path(r'^api/hub-data/$', HubDataApiView.as_view(), name='hub-data-api'),
    re_path(r'^manage/$', HubManageView.as_view(), name="hub-manage"),
    re_path(r'^request/$', HubRequestView.as_view(), name="hub-request"),
]
