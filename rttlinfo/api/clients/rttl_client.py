import requests
import logging
from typing import Dict, List, Optional, Union
from django.conf import settings
from django.core.cache import cache
import hashlib
import json
# from rttlinfo.dataclasses import Course, CourseStatus, CourseConfiguration

logger = logging.getLogger(__name__)


class RttlApiError(Exception):
    """
    Custom exception for RTTL API errors.
    """
    def __init__(
            self, message: str,
            status_code: int = None,
            response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class RttlApiClient:
    """
    Simplified API client for the RTTL REST API.
    Uses Django's cache framework for optional caching instead of database
    tables.
    """

    def __init__(
            self,
            base_url: str = None,
            api_key: str = None,
            version: str = "v1",
            cache_timeout: int = 300):
        self.base_url = base_url or getattr(
            settings, 'RTTL_BASE_URL', 'https://jupyter.eval.rttl.uw.edu')
        self.api_key = api_key or getattr(settings, 'RTTL_API_KEY', None)
        self.version = version
        self.cache_timeout = cache_timeout  # 5 minutes default
        self.session = requests.Session()

        if not self.api_key:
            raise ValueError("RTTL API key is required. Set RTTL_API_KEY in \
                             settings or pass api_key parameter.")

        # Set default headers
        self.session.headers.update({
            'Authorization': f'Bearer Api-Key {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _get_url(self, endpoint: str) -> str:
        """
        Construct full URL for an endpoint.
        """
        return f"{self.base_url}/api/{self.version}/{endpoint.lstrip('/')}"

    def _get_cache_key(
            self,
            method: str,
            endpoint: str,
            params: dict = None) -> str:
        """
        Generate cache key for request.
        """
        key_data = f"{method}:{endpoint}"
        if params:
            key_data += f":{json.dumps(params, sort_keys=True)}"
        return f"rttl_api:{hashlib.md5(key_data.encode()).hexdigest()}"

    def _make_request(
            self,
            method: str,
            endpoint: str,
            use_cache: bool = True,
            **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling, logging, and optional caching.
        """
        url = self._get_url(endpoint)

        # Check cache for GET requests
        cache_key = None
        if method == 'GET' and use_cache and self.cache_timeout > 0:
            cache_key = self._get_cache_key(
                method,
                endpoint,
                kwargs.get('params'))
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit: {method} {url}")

                # Create a mock response object
                class MockResponse:
                    def __init__(self, data, status_code=200):
                        self._json = data
                        self.status_code = status_code
                        self.content = json.dumps(data).encode()

                    def json(self):
                        return self._json

                    def raise_for_status(self):
                        pass

                return MockResponse(cached_response)

        try:
            response = self.session.request(method, url, **kwargs)

            # Log the request for debugging
            logger.debug(f"{method} {url} - Status: {response.status_code}")

            # Cache successful GET responses
            if (method == 'GET' and use_cache and self.cache_timeout > 0 and
                    response.status_code == 200 and cache_key):
                try:
                    response_data = response.json()
                    cache.set(cache_key, response_data, self.cache_timeout)
                    logger.debug(f"Cached response: {cache_key}")
                except (ValueError, TypeError):
                    pass  # Skip caching if response isn't JSON

            # Raise for HTTP errors
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {url} - {str(e)}")
            status_code = getattr(
                e.response,
                'status_code',
                None) if hasattr(e, 'response') else None
            response_data = None

            if hasattr(e, 'response') and e.response is not None:
                try:
                    response_data = e.response.json()
                except Exception:
                    pass

            raise RttlApiError(
                f"API request failed: {str(e)}",
                status_code,
                response_data)

    def _handle_response(
            self,
            response: requests.Response) -> Union[Dict, List]:
        """
        Handle API response and return JSON data.
        """
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            raise RttlApiError(
                f"Invalid JSON response: {str(e)}",
                response.status_code)

    # Course methods
    def list_courses(
            self,
            sis_id: str = None,
            use_cache: bool = True) -> List[Dict]:
        """
        List courses.

        Args:
            sis_id: Optional SIS ID to filter by
            use_cache: Whether to use cached results

        Returns:
            List of course dictionaries
        """
        params = {'sis_id': sis_id} if sis_id else {}

        # Temp override for dev
        # params = {"sis_id": '2025-spring-BANA-310-B'}

        response = self._make_request(
            'GET',
            'courses/',
            params=params,
            use_cache=use_cache)
        # return
        # [Course.from_api_data(i) for i in self._handle_response(response)]
        return self._handle_response(response)

    def get_course(self, course_id: int, use_cache: bool = True) -> Dict:
        """
        Get course details by ID.

        Args:
            course_id: Course ID
            use_cache: Whether to use cached results

        Returns:
            Course dictionary with details and statuses
        """
        response = self._make_request(
            'GET', f'courses/{course_id}/',
            use_cache=use_cache)
        return self._handle_response(response)

    def create_course(self, course_data: Dict) -> Dict:
        """
        Create a new course.

        Args:
            course_data: Course data dictionary

        Returns:
            Created course dictionary
        """
        response = self._make_request(
            'POST',
            'courses/',
            json=course_data,
            use_cache=False)
        return self._handle_response(response)

    def update_course(self, course_id: int, course_data: Dict) -> Dict:
        """
        Update an existing course.

        Args:
            course_id: Course ID to update
            course_data: Updated course data

        Returns:
            Updated course dictionary
        """
        response = self._make_request(
            'PUT',
            f'courses/{course_id}/',
            json=course_data, use_cache=False)
        return self._handle_response(response)

    def delete_course(self, course_id: int) -> bool:
        """
        Delete a course.

        Args:
            course_id: Course ID to delete

        Returns:
            True if successful
        """
        response = self._make_request(
            'DELETE',
            f'courses/{course_id}/',
            use_cache=False)
        return response.status_code == 204

    # Course Status methods
    def list_course_statuses(
            self,
            course_id: int,
            configs: bool = None,
            use_cache: bool = True) -> List[Dict]:
        """
        List statuses for a specific course.

        Args:
            course_id: Course ID
            configs: If True, limit to statuses with configuration objects
            use_cache: Whether to use cached results

        Returns:
            List of course status dictionaries
        """
        params = {'configs': configs} if configs is not None else {}
        response = self._make_request(
            'GET',
            f'courses/{course_id}/status/',
            params=params,
            use_cache=use_cache)
        return self._handle_response(response)

    def get_course_status(
            self,
            course_id: int,
            status_id: int,
            use_cache: bool = True) -> Dict:
        """
        Get specific course status details.

        Args:
            course_id: Course ID
            status_id: Status ID
            use_cache: Whether to use cached results

        Returns:
            Course status dictionary
        """
        response = self._make_request(
            'GET',
            f'courses/{course_id}/status/{status_id}/',
            use_cache=use_cache)
        return self._handle_response(response)

    def create_course_status(self, course_id: int, status_data: Dict) -> Dict:
        """
        Create a new status for a course.

        Args:
            course_id: Course ID
            status_data: Status data dictionary

        Returns:
            Created status dictionary
        """
        response = self._make_request(
            'POST',
            f'courses/{course_id}/status/',
            json=status_data, use_cache=False)
        return self._handle_response(response)

    def update_course_status(
            self,
            course_id: int,
            status_id: int,
            status_data: Dict) -> Dict:
        """
        Update an existing course status.

        Args:
            course_id: Course ID
            status_id: Status ID
            status_data: Updated status data

        Returns:
            Updated status dictionary
        """
        response = self._make_request(
            'PUT',
            f'courses/{course_id}/status/{status_id}/',
            json=status_data, use_cache=False)
        return self._handle_response(response)

    def delete_course_status(self, course_id: int, status_id: int) -> bool:
        """
        Delete a course status.

        Args:
            course_id: Course ID
            status_id: Status ID

        Returns:
            True if successful
        """
        response = self._make_request(
            'DELETE',
            f'courses/{course_id}/status/{status_id}/',
            use_cache=False)
        return response.status_code == 204

    def create_or_update_course_status(self, status_data: Dict) -> Dict:
        """
        Convenience method to create course and/or status in one call.

        Args:
            status_data: Status update data including sis_course_id

        Returns:
            Dictionary with 'course' and 'status' keys
        """
        response = self._make_request(
            'POST',
            'coursestatus/',
            json=status_data,
            use_cache=False)
        return self._handle_response(response)

    # Course Configuration methods
    def list_course_configs(
            self,
            course_id: int,
            applied: bool = None,
            use_cache: bool = True) -> List[Dict]:
        """
        List configurations for a specific course.

        Args:
            course_id: Course ID
            applied: If True, only show applied configurations
            use_cache: Whether to use cached results

        Returns:
            List of configuration dictionaries
        """
        params = {'applied': applied} if applied is not None else {}
        response = self._make_request(
            'GET',
            f'courses/{course_id}/configs/',
            params=params,
            use_cache=use_cache)
        return self._handle_response(response)

    # Admin Course methods
    def list_admin_courses(
            self,
            sis_id: str = None,
            use_cache: bool = True) -> List[Dict]:
        """
        List admin courses.

        Args:
            sis_id: Optional SIS ID to filter by
            use_cache: Whether to use cached results

        Returns:
            List of admin course dictionaries
        """
        params = {'sis_id': sis_id} if sis_id else {}
        response = self._make_request(
            'GET',
            'admincourses/',
            params=params,
            use_cache=use_cache)
        return self._handle_response(response)

    def get_admin_course(
            self,
            admin_course_id: int,
            use_cache: bool = True) -> Dict:
        """
        Get admin course details by ID.

        Args:
            admin_course_id: Admin course ID
            use_cache: Whether to use cached results

        Returns:
            Admin course dictionary with full details
        """
        response = self._make_request(
            'GET',
            f'admincourses/{admin_course_id}/',
            use_cache=use_cache)
        return self._handle_response(response)

    # Utility methods
    def get_course_by_sis_id(
            self,
            sis_course_id: str,
            use_cache: bool = True) -> Optional[Dict]:
        """
        Get course by SIS ID.

        Args:
            sis_course_id: SIS course ID
            use_cache: Whether to use cached results

        Returns:
            Course dictionary or None if not found
        """
        courses = self.list_courses(sis_id=sis_course_id, use_cache=use_cache)
        return courses[0] if courses else None

    def clear_cache(self, pattern: str = None):
        """
        Clear cached API responses.

        Args:
            pattern: Optional pattern to match cache keys
            (not implemented in basic Django cache)
        """
        # Django's basic cache doesn't support pattern deletion
        # This would need to be implemented with Redis or similar
        logger.warning("Cache clearing not implemented for basic Django cache \
                       backend")

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics (limited with Django's basic cache).
        """
        return {
            'backend': getattr(
                settings,
                'CACHES', {}).get('default', {}).get('BACKEND', 'unknown'),
            'timeout': self.cache_timeout,
            'note': 'Full cache stats require Redis or Memcached backend'
        }


# Convenience functions for common operations
def get_rttl_client(
        use_cache: bool = True,
        cache_timeout: int = 300) -> RttlApiClient:
    """
    Get configured RTTL API client instance.

    Args:
        use_cache: Whether to enable caching by default
        cache_timeout: Cache timeout in seconds
    """
    return RttlApiClient(cache_timeout=cache_timeout if use_cache else 0)


def get_course_status_by_sis_id(
        sis_course_id: str,
        use_cache: bool = True) -> Optional[Dict]:
    """
    Quick function to get course status by SIS ID.

    Args:
        sis_course_id: SIS course ID
        use_cache: Whether to use cached results

    Returns:
        Course data with latest status or None
    """
    client = get_rttl_client(use_cache=use_cache)
    return client.get_course_by_sis_id(sis_course_id, use_cache=use_cache)


# Backwards compatibility with original client
class RttlApiClient_Legacy:
    """
    Legacy client for backwards compatibility.
    """

    def __init__(self, api_key=None):
        self.client = get_rttl_client()

    def get_course_status(self, course_sis_id):
        """
        Legacy method - returns raw response like original.
        """
        try:
            courses = self.client.list_courses(sis_id=course_sis_id)
            return courses
        except RttlApiError as e:
            # Return error in format similar to requests
            class MockResponse:
                def __init__(self, error_msg, status_code):
                    self.error = error_msg
                    self.status_code = status_code

                def json(self):
                    return {"error": self.error}

            return MockResponse(e.message, e.status_code)
