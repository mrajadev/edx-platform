"""
Utilities for waffle usage, including namespacing and caching.
"""
from abc import ABCMeta
from contextlib import contextmanager
import logging

from request_cache import get_request, get_cache as get_request_cache
from waffle.testutils import override_switch as waffle_override_switch
from waffle import flag_is_active, switch_is_active

from .models import CourseOverrideWaffleFlagModel

log = logging.getLogger(__name__)


class WafflePlus(object):
    """
    Waffle helper class that provides native support for
    namespacing waffle settings and caching within a request.
    """
    __metaclass__ = ABCMeta

    def __init__(self, namespace, log_prefix=None):
        """
        Initializes the waffle plus instance.

        Arguments:
            namespace (String): Namespace string appended to start of all waffle
                flags and switches (e.g. "grades")
            log_prefix (String): Optional string to be appended to log messages
                (e.g. "Grades: ")

        """
        self.namespace = namespace
        self.log_prefix = log_prefix

    def _namespaced_name(self, setting_name):
        """
        Returns the namespaced name of the waffle switch/flag.
        """
        assert self.namespace, "You must provide a namespace for waffle plus."
        return u'{}.{}'.format(self.namespace, setting_name)

    @staticmethod
    def _get_request_cache():
        """
        Returns the request cache used by WafflePlus classes.
        """
        return get_request_cache('WafflePlus')


class WaffleSwitchPlus(WafflePlus):
    """
    Waffle Switch helper class that provides native support for namespacing
    waffle switches and caching within a request.

    """
    def is_enabled(self, switch_name):
        """
        Returns and caches whether the given waffle switch is enabled.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        value = self._cached_switches.get(namespaced_switch_name)
        if value is None:
            value = switch_is_active(namespaced_switch_name)
            self._cached_switches[namespaced_switch_name] = value
        return value

    @contextmanager
    def override(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the request cache AND in the model.
        """
        previous_active = self.is_enabled(switch_name)
        try:
            self.override_for_request(switch_name, active)
            with self.override_in_model(switch_name, active):
                yield
        finally:
            self.override_for_request(switch_name, previous_active)

    def override_for_request(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the remainder of
        this request (as this is not a context manager).
        Note: The value is overridden in the request cache, not in the model.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        self._cached_switches[namespaced_switch_name] = active
        log.info(u"%sSwitch '%s' set to %s for request.", self.log_prefix, namespaced_switch_name, active)

    @contextmanager
    def override_in_model(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the model, not the request cache.
        """
        namespaced_switch_name = self._namespaced_name(switch_name)
        with waffle_override_switch(namespaced_switch_name, active):
            log.info(u"%sSwitch '%s' set to %s in model.", self.log_prefix, namespaced_switch_name, active)
            yield

    @property
    def _cached_switches(self):
        """
        Returns cached active values of all switches in this namespace.
        """
        return self._all_cached_switches.setdefault(self.namespace, {})

    @property
    def _all_cached_switches(self):
        """
        Returns dictionary of all switches in the request cache,
        keyed by namespace.
        """
        return self._get_request_cache().setdefault('switches', {})


class WaffleFlagPlus(WafflePlus):
    """
    Waffle helper class that provides native support for
    namespacing waffle flags and caching within a request.
    """
    __metaclass__ = ABCMeta

    def __init__(self, namespace, log_prefix=None, course_flags=None):
        """
        Initializes the waffle flag plus instance.

        Arguments:
            namespace (String): Namespace string appended to start of all waffle
                flags and switches (e.g. "grades")
            log_prefix (String): Optional string to be appended to log messages
                (e.g. "Grades: ")
            course_flags (Sequence): A sequence of string flag names that
                require a course_id when calling is_enabled, to first check
                for a course override.

        """
        super(WaffleFlagPlus, self).__init__(namespace, log_prefix)
        self.course_flags = course_flags if course_flags else ()

    @property
    def _cached_flags(self):
        """
        Returns a dictionary of all flags in the request cache.
        """
        return self._get_request_cache().setdefault('flags', {})

    def is_enabled(self, flag_name, course_id=None):
        """
        Returns and caches whether the given waffle flag is active for the
        request, including when forced on/off at the course level.

        Arguments:
            flag_name (String): The name of the flag to check.
            course_id (CourseLocator): The optional course to check for override before
                checking the waffle.  If used, the flag_name must be registered
                as a course_flag.

        """
        # validate arguments
        if course_id:
            assert flag_name in self.course_flags, "Waffle flag '{}' is not one of the known course flags: {}".format(
                flag_name, self.course_flags)
        elif (flag_name in self.course_flags):
            assert course_id, "The course_id is required when checking this waffle flag."

        namespaced_flag_name = self._namespaced_name(flag_name)
        value = self._cached_flags.get(namespaced_flag_name)
        if value is None:
            # first check if waffle flag is forced on or off for the course.
            force_override = CourseOverrideWaffleFlagModel.override_value(flag_name, course_id)

            if force_override == CourseOverrideWaffleFlagModel.ALL_CHOICES.on:
                value = True
            elif force_override == CourseOverrideWaffleFlagModel.ALL_CHOICES.off:
                value = False
            else:
                # otherwise, check waffle.
                value = flag_is_active(get_request(), namespaced_flag_name)

            self._cached_flags[namespaced_flag_name] = value
        return value
