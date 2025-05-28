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

    RESTCLIENTS_CANVAS_DAO_CLASS = 'Live'
    RESTCLIENTS_CANVAS_HOST = 'example.instructure.com'
    RESTCLIENTS_CANVAS_OAUTH_BEARER = '...'

**BLTI settings**

[django-blti settings](https://github.com/uw-it-aca/django-blti#project-settingspy)

Project urls.py
---------------
    url(r'^rttlinfo/', include('rttlinfo.urls')),
