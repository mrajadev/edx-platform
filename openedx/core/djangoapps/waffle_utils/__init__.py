"""
Utilities for waffle.

Includes namespacing, caching, and course overrides for waffle flags.

For testing WaffleFlags, see testutils.py.
For testing WaffleSwitchNamespace, use its context manager.

"""
from abc import ABCMeta
from contextlib import contextmanager
import logging
from waffle.testutils import override_switch as waffle_override_switch
from waffle import flag_is_active, switch_is_active

from opaque_keys.edx.keys import CourseKey
from request_cache import get_request, get_cache as get_request_cache

from .models import CourseOverrideWaffleFlagModel

log = logging.getLogger(__name__)


class WaffleNamespace(object):
    """
    A base class for a request cached namespace for waffle flags/switches.

    Once an instance of this class is configured with a namespace
    (e.g. "my_namespace"), all subclass methods that take a flag or switch name
    (e.g. "my_flagname") will use a longer namespaced name in waffle
    (e.g. "my_namespace.my_flagname").

    """
    __metaclass__ = ABCMeta

    def __init__(self, namespace, log_prefix=None):
        """
        Initializes the waffle namespace instance.

        Arguments:
            namespace (String): Namespace string appended to start of all waffle
                flags and switches (e.g. "grades")
            log_prefix (String): Optional string to be appended to log messages
                (e.g. "Grades: ")

        """
        assert namespace, "The namespace is required."
        self.namespace = namespace
        self.log_prefix = log_prefix

    def _namespaced_name(self, setting_name):
        """
        Returns the namespaced name of the waffle switch/flag.

        For example, the namespaced name of the waffle switch/flag would be:
            my_namespace.my_setting_name

        Arguments:
            setting_name (String): The name of the flag or switch.

        """
        return u'{}.{}'.format(self.namespace, setting_name)

    @staticmethod
    def _get_namespace_request_cache():
        """
        Returns the request cache used by WaffleNamespace classes.
        """
        return get_request_cache('WaffleNamespace')


class WaffleSwitchNamespace(WaffleNamespace):
    """
    Provides a request cached namespace for waffle switches.
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
        Returns a dictionary of all namespaced switches in the request cache.
        """
        return self._get_namespace_request_cache().setdefault('switches', {})


class WaffleFlagNamespace(WaffleNamespace):
    """
    Provides a request cached namespace for waffle flags.
    """
    __metaclass__ = ABCMeta

    @property
    def _cached_flags(self):
        """
        Returns a dictionary of all namespaced flags in the request cache.
        """
        return self._get_namespace_request_cache().setdefault('flags', {})

    def is_enabled(self, flag_name, check_before_waffle_callback=None):
        """
        Returns and caches whether the given flag is enabled.

        If the flag value is already cached in the request, it is returned.
        If check_before_waffle_callback is supplied, it is called before
            checking waffle.
        If check_before_waffle_callback returns None, or if it is not supplied,
            then waffle is used to check the flag.

        Arguments:
            flag_name (String): The name of the flag to check.
            check_before_waffle_callback (function): (Optional) A function that
                will be checked before continuing on to waffle. If
                check_before_waffle_callback(namespaced_flag_name) returns True
                or False, it is cached and returned.  If it returns None, then
                waffle is used.

        """
        # validate arguments
        namespaced_flag_name = self._namespaced_name(flag_name)
        value = self._cached_flags.get(namespaced_flag_name)

        if value is None:
            if check_before_waffle_callback:
                value = check_before_waffle_callback(namespaced_flag_name)

            if value is None:
                value = flag_is_active(get_request(), namespaced_flag_name)

            self._cached_flags[namespaced_flag_name] = value
        return value


class WaffleFlag(object):
    """
    Represents a single waffle flag, using a cached waffle namespace.
    """

    def __init__(self, waffle_namespace, flag_name):
        """
        Initializes the waffle flag instance.

        Arguments:
            waffle_namespace (WaffleFlagNamespace): Provides a cached namespace
                for this flag.
            flag_name (String): The name of the flag (without namespacing).

        """
        self.waffle_namespace = waffle_namespace
        self.flag_name = flag_name

    def is_enabled(self):
        """
        Returns whether or not the flag is enabled.
        """
        return self.waffle_namespace.is_enabled(self.flag_name)


class CourseOverrideWaffleFlag(WaffleFlag):
    """
    Represents a single waffle flag that can be forced on/off for a course.

    Uses a cached waffle namespace.

    """

    def _get_course_override_callback(self, course_id):
        """
        Returns a function to use as the check_before_waffle_callback.

        Arguments:
            course_id (CourseKey): The course to check for override before
            checking waffle.

        """
        def course_override_callback(namespaced_flag_name):
            """
            Returns True/False if the flag was forced on or off for the provided
            course.  Returns None if the flag was not overridden.

            Arguments:
                namespaced_flag_name (String): A namespaced version of the flag
                    to check.

            """
            force_override = CourseOverrideWaffleFlagModel.override_value(namespaced_flag_name, course_id)

            if force_override == CourseOverrideWaffleFlagModel.ALL_CHOICES.on:
                return True
            if force_override == CourseOverrideWaffleFlagModel.ALL_CHOICES.off:
                return False
            return None
        return course_override_callback

    def is_enabled(self, course_id=None):
        """
        Returns whether or not the flag is enabled.

        Arguments:
            course_id (CourseKey): The course to check for override before
            checking waffle.

        """
        # validate arguments
        assert issubclass(type(course_id), CourseKey), "The course_id '{}' must be a CourseKey.".format(str(course_id))

        return self.waffle_namespace.is_enabled(
            self.flag_name,
            check_before_waffle_callback=self._get_course_override_callback(course_id)
        )
