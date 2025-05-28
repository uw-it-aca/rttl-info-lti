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

        data = self.api_client.get_course_status(course_sis_id)
        cache.set(cache_key, data, timeout=3600)
        return data
