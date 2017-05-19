"""
Test utilities for waffle plus utilities.
"""

from functools import wraps

from waffle.testutils import override_flag as waffle_override_flag


def override_flag_plus(waffle_flag_plus, name, active):
    """
    To be used as a decorator for a test function to override a waffle plus
    flag.

        waffle_flag_plus (WaffleFlagPlus): The instance with the proper
            namespacing for the provided flag.
        name (String): The name of the flag.
        active (Boolean): The value to which the flag will be set.

    Example usage:

        @override_flag_plus(course_experience_config(), UNIFIED_COURSE_EXPERIENCE_FLAG, active=True)

        Where course_experience_config() is a function that returns a
        WaffleFlagPlus instance.

    """
    def real_decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):
            namespaced_name = waffle_flag_plus._namespaced_name(name)

            # save previous value
            flag_existed = namespaced_name in waffle_flag_plus._cached_flags
            if flag_existed:
                previous_active = waffle_flag_plus._cached_flags[namespaced_name]

            # set new value
            waffle_flag_plus._cached_flags[namespaced_name] = active

            with waffle_override_flag(namespaced_name, active):
                # call wrapped function
                function(*args, **kwargs)

            # restore value
            if flag_existed:
                waffle_flag_plus._cached_flags[namespaced_name] = previous_active
            elif namespaced_name in waffle_flag_plus._cached_flags:
                del waffle_flag_plus._cached_flags[namespaced_name]
        return wrapper

    return real_decorator
