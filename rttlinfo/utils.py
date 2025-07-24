import re
from uw_sws import term as sws_term
from django.core.cache import cache
from datetime import datetime, time, timedelta
from logging import getLogger
logger = getLogger(__name__)


def get_term_from_string(term_string):
    """
    Convert a term string to a term integer.
    """
    try:
        # Check if the term string is a number
        term = int(term_string)
        if term < 1 or term > 4:
            raise Exception(f"Term must be between 1 and 4, got {term}")
        return term
    except ValueError:
        pass
    term_string = term_string.lower()
    if term_string in ["winter", "win", "wi"]:
        return 1
    elif term_string in ["spring", "spr", "sp"]:
        return 2
    elif term_string in ["summer", "sum", "su"]:
        return 3
    elif term_string in ["autumn", "aut", "au"]:
        return 4
    else:
        raise ValueError(f"Invalid term string: {term_string}")


def validate_source_sis(source_sis):
    """
    Validate the source SIS ID.
    Note: Cannot find a canonical source for allowed characters in curriculum
        codes, but a quick review of UWSDBDataStore.sec.sr_curric_code
        (curric_abbr) shows only A-Z, & and space are being used.
    Note: non-standard IDs are possible for non-canvas courses, but irrelevant
    to this app.
    """
    COURSE_SIS_REGEX = \
        "^([0-9]{4})-(autumn|winter|spring|summer){1}-([A-Z& ]+)-(.*)$"

    if not source_sis:
        raise ValueError("Source SIS ID cannot be empty.")

    sis = re.match(COURSE_SIS_REGEX, source_sis)
    if not sis:
        raise ValueError(f"Invalid source SIS ID format: {source_sis}")

    return source_sis, sis


def get_course_eligibility(course_sis):
    """
    Determine if a course is eligible for the RTTL service based on its SIS ID.
    Note: this is a naive check based on the term and year in the SIS ID, and
    won't check other policy requirements like enrollments.
    """
    logger.debug(f"Checking course eligibility for SIS ID: {course_sis}")
    try:
        # This also handles the case where source_sis is None or empty
        source_sis, sis = validate_source_sis(course_sis)
        course_year = int(sis.groups()[0])
        course_term = get_term_from_string(sis.groups()[1])
    except ValueError as e:
        return False
    today = datetime.now().date()
    if course_year > today.year:
        # We can skip calling sws_term.get_current_term() here
        return True
    current_term = get_term_from_sws()
    logger.debug(f"Current term: {current_term}")
    if course_year < current_term['year']:
        return False
    if course_year == current_term['year'] and \
            course_term < get_term_from_string(current_term['quarter']):
        return False
    return True


def get_term_from_sws(use_cache=True):
    """
    Get the current term from SWS or from cache if available.
    If not a cache hit, then the timeout should be the amount of time between
    now and 11:59:59 PM
    """
    cache_key = 'current_term_sws'

    if use_cache:
        # Try to get from cache first
        cached_term = cache.get(cache_key)
        if cached_term is not None:
            return cached_term

    # Cache miss or cache disabled - fetch from SWS
    current_term = sws_term.get_current_term()
    # Term obj contains weakrefs, so only cache JSON data
    cacheable_current_term = current_term.json_data()

    if use_cache:
        # Calculate timeout until 11:59:59 PM today
        now = datetime.now()
        end_of_day = datetime.combine(now.date(), time(23, 59, 59))

        # If it's already past 11:59:59 PM, set timeout for tomorrow
        if now >= end_of_day:
            end_of_day = end_of_day + timedelta(days=1)

        timeout_seconds = int((end_of_day - now).total_seconds())

        # Cache the result with calculated timeout
        cache.set(cache_key, cacheable_current_term, timeout_seconds)

    return cacheable_current_term
