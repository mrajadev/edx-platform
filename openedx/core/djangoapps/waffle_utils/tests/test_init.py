"""
Tests for waffle utils features.
"""
import ddt
from django.test import TestCase
from mock import patch
from opaque_keys.edx.keys import CourseKey
from waffle.testutils import override_flag

from request_cache.middleware import RequestCache

from .. import CourseWaffleFlag, WaffleFlagNamespace
from ..models import WaffleFlagCourseOverrideModel


@ddt.ddt
class TestCourseWaffleFlag(TestCase):
    """
    Tests the CourseWaffleFlag.
    """

    @ddt.data(
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.on, 'waffle_enabled': False, 'result': True},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.off, 'waffle_enabled': True, 'result': False},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.unset, 'waffle_enabled': True, 'result': True},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.unset, 'waffle_enabled': False, 'result': False},
    )
    def test_course_waffle_flag(self, data):
        """
        Tests various combinations of a flag being set in waffle and overridden
        for a course.
        """
        namespace_name = "test_namespace"
        flag_name = "test_flag"
        namespaced_flag_name = namespace_name + "." + flag_name

        course_key = CourseKey.from_string("edX/DemoX/Demo_Course")
        namespace = WaffleFlagNamespace(namespace_name)
        course_flag = CourseWaffleFlag(namespace, flag_name)

        RequestCache.clear_request_cache()

        with patch.object(WaffleFlagCourseOverrideModel, 'override_value', return_value=data['course_override']):
            with override_flag(namespaced_flag_name, active=data['waffle_enabled']):
                # check twice to test that the result is properly cached
                self.assertEqual(course_flag.is_enabled(course_key), data['result'])
                self.assertEqual(course_flag.is_enabled(course_key), data['result'])
                # result is cached, so override check should happen once
                WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(namespaced_flag_name, course_key)
