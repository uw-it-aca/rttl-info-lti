# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.apps import AppConfig
import os


class RttlInfoConfig(AppConfig):
    name = 'rttlinfo'
    path = os.path.dirname(os.path.abspath(__file__))
