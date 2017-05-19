"""
Unified course experience settings and helper methods.
"""
import waffle

from openedx.core.djangoapps.waffle_utils import WaffleFlagPlus
from request_cache.middleware import RequestCache

# Waffle flag to enable the full screen course content view along with a unified
# course home page.
# NOTE: This is the only legacy flag that does not use the namespace.
UNIFIED_COURSE_VIEW_FLAG = 'unified_course_view'

# Namespace for the waffle flags that follow.
WAFFLE_NAMESPACE = u'course_experience'

# Waffle flag to enable a single unified "Course" tab.
UNIFIED_COURSE_EXPERIENCE_FLAG = 'unified_course_experience'


def course_experience_config():
    """
    Returns a waffle plus object for course experience scoped waffle flags.
    """
    return WaffleFlagPlus(namespace=WAFFLE_NAMESPACE, log_prefix=u'Course Experience: ', course_flags=(UNIFIED_COURSE_EXPERIENCE_FLAG))


def default_course_url_name(request=None):
    """
    Returns the default course URL name for the current user.
    """
    if waffle.flag_is_active(request or RequestCache.get_current_request(), UNIFIED_COURSE_VIEW_FLAG):
        return 'openedx.course_experience.course_home'
    else:
        return 'courseware'


def course_home_url_name(course_id):
    """
    Returns the course home page's URL name for the current user.
    """
    if course_experience_config().is_enabled(UNIFIED_COURSE_EXPERIENCE_FLAG, course_id):
        return 'openedx.course_experience.course_home'
    else:
        return 'info'
