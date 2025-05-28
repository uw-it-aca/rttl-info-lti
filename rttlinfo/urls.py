# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from rttlinfo.views import LaunchView, HubDetailsView # HubRequestView  # CourseDetailsView

urlpatterns = [
    re_path(r'^$', LaunchView.as_view(), name="lti-launch"),
    # re_path(r'^$',  RttlInfoLaunchView.as_view(), name="lti-launch"),
    re_path(r'^details/$', HubDetailsView.as_view(), name="hub-details"),
    # re_path(r'^request/$', HubRequestView.as_view(), name="hub-request"),
]


# from django.urls import re_path
# from rttlinfo.views import RttlInfoLaunchView, HubDetailsView, JupyterHubStatusView


# urlpatterns = [
#     re_path(r'^$', RttlInfoLaunchView.as_view(), name="lti-launch"),
#     # re_path(r'^course/details/$', CourseDetailsView.as_view(), name="course-details"),
#     re_path(r'^details/$', HubDetailsView.as_view(), name="hub-details"),
#     re_path(r'^api/jupyterhub/status/$', JupyterHubStatusView.as_view(), name="jupyterhub-status"),
# ]