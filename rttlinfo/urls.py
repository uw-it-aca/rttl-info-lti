# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache

from django.urls import path
from .views import \
    LaunchView, \
    HubDataApiView, \
    HubRequestView, \
    HubManageView, \
    HubStatusApiView, \
    HubUpdateConfigView

urlpatterns = [
    path('', LaunchView.as_view(), name='lti-launch'),
    path('api/hub-data/', HubDataApiView.as_view(), name='hub-data-api'),
    path('manage/', HubManageView.as_view(), name="hub-manage"),
    path('request/', HubRequestView.as_view(), name="hub-request"),

    # path('request/', HubRequestView.as_view(), name='hub-request'),
    # path('manage/', HubManageView.as_view(), name='hub-manage'),
    # path('api/hub-status/', HubStatusApiView.as_view(), name='hub-status-api'),
    # path('update-config/', HubUpdateConfigView.as_view(), name='hub-update-config'),
    # ... other patterns ...
]
