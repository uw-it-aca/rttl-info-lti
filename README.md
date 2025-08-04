# UW RTTL Info LTI App

[![Build Status](https://github.com/uw-it-aca/rttl-info-lti/workflows/Build%2C%20Test%20and%20Deploy/badge.svg?branch=main)](https://github.com/uw-it-aca/rttl-info-lti/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/rttl-info-lti/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/rttl-info-lti?branch=main)

An LTI tool for request and status on RTTL course resources.

Project settings.py
------------------

**INSTALLED_APPS**

    'rttlinfo',
    'blti',

**REST client app settings**

    RTTL_API_KEY = 'Valid_RTTL_REST API key'

**BLTI settings**

[django-blti settings](https://github.com/uw-it-aca/django-blti#project-settingspy)

Project urls.py
---------------
    Assuming the ingress URL is `https://example.com/rttlinfo/`
    re_path(r'^rttlinfo/', include('rttlinfo.urls')),
    re_path(r'^rttlinfo/blti/', include('blti.urls')),
