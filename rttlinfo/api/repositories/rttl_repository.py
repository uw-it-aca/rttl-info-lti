from django.core.cache import cache
from rttlinfo.api.clients.rttl_client import RttlApiClient


class RttlInfoRepository:
    def __init__(self, api_client=None):
        self.api_client = api_client or RttlApiClient()

    def get_course_status(self, course_sis_id):
        cache_key = f"course_status:{course_sis_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # data = self.api_client.get_course_status(course_sis_id)
        data = self.api_client.list_courses(course_sis_id)
        # cache.set(cache_key, data, timeout=3600)
        # one hour may be too long, especially during development
        cache.set(cache_key, data, timeout=30)
        return data

    def get_course_details(self, course_sis_id):
        cache_key = f"course_details:{course_sis_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get course status first to retrieve the course ID
        status_data = self.get_course_status(course_sis_id)

        data = self.api_client.get_course(status_data[0]['id'])
        cache.set(cache_key, data, timeout=30)
        return data

    def get_course_configs(self, course_sis_id):
        cache_key = f"course_configs:{course_sis_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get course status first to retrieve the course ID
        status_data = self.get_course_status(course_sis_id)

        data = self.api_client.list_course_configs(status_data[0]['id'])
        cache.set(cache_key, data, timeout=30)
        """
        Return data looks something like this:
        [
            {
                'configuration_applied': False,
                'cpu_request': 2,
                'memory_request': 3,
                'storage_request': 4,
                'image_uri': 'https://example.com/imagename',
                'image_tag': 'main',
                'features_request': '',
                'gitpuller_targets': [],
                'configuration_comments': 'heyhey',
                'create_timestamp': '2025-06-03T15:43:40.567793-07:00'
            }
        ]
        """
        return data
