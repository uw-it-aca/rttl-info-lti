# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache

from django.urls import path, re_path
from .views import \
    LaunchView, \
    HubDataApiView, \
    HubRequestView, \
    HubManageView

# urlpatterns = [
#     path('', LaunchView.as_view(), name='lti-launch'),
#     path('api/hub-data/', HubDataApiView.as_view(), name='hub-data-api'),
#     path('manage/', HubManageView.as_view(), name="hub-manage"),
#     path('request/', HubRequestView.as_view(), name="hub-request"),
# ]

urlpatterns = [
    re_path(r'^$', LaunchView.as_view(), name='lti-launch'),
    re_path(r'^api/hub-data/$', HubDataApiView.as_view(), name='hub-data-api'),
    re_path(r'^manage/$', HubManageView.as_view(), name="hub-manage"),
    re_path(r'^request/$', HubRequestView.as_view(), name="hub-request"),
]