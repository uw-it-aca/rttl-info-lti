import requests
from django.conf import settings
# import urllib3

# # Disable InsecureRequestWarning
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# TODO: add caching

class RttlApiClient:
    BASE_URL = "https://jupyter.eval.rttl.uw.edu/api/v1/"
    
    def __init__(self, api_key=None):
        # self.api_key = api_key or settings.RTTL_API_KEY
        # self.session = requests.Session()
        # self.session.headers.update({"Authorization": f"Bearer API-Key {self.api_key}"})
        pass
    
    def get_course_status(self, course_sis_id):
        # url = f"{self.BASE_URL}courses/?sis_id={course_sis_id}"
        # response = self.session.get(url, verify=False)
        # response.raise_for_status()  # Raises exception for 4XX/5XX responses
        url = f"{self.BASE_URL}courses/"
        # querystring = {"sis_id":course_sis_id}
        # querystring = {"sis_id": "2025-spring-TEST-101-A"}
        querystring = {"sis_id": '2025-spring-BANA-310-B'}

        payload = ""
        headers = {"Authorization": f"Bearer Api-Key { settings.RTTL_API_KEY }"}

        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

        return response.json()