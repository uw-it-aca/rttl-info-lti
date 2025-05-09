# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.urls import re_path
from rttlinfo.views import RttlInfoLaunchView


urlpatterns = [
    re_path(r'^$',  RttlInfoLaunchView.as_view(), name="lti-launch"),
]
