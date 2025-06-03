# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from rttlinfo.views import LaunchView, HubManageView, HubRequestView

urlpatterns = [
    re_path(r'^$', LaunchView.as_view(), name="lti-launch"),
    # re_path(r'^$',  RttlInfoLaunchView.as_view(), name="lti-launch"),
    re_path(r'^manage/$', HubManageView.as_view(), name="hub-manage"),
    re_path(r'^request/$', HubRequestView.as_view(), name="hub-request"),
]
