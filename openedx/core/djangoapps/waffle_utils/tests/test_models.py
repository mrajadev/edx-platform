"""
Tests for the models that control
the waffle util configuration.
"""
from ddt import data, ddt, unpack
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from request_cache.middleware import RequestCache

from ..models import WaffleFlagCourseOverrideModel


@ddt
class WaffleFlagCourseOverrideTests(TestCase):
    """
    Tests the behavior of the waffle flags specific to individual
    courses, assuring that forcible setting of flags works as
    expected and that the disabled flag restricts this behavior.
    """

    WAFFLE_TEST_NAME = "waffle_test_course_override"
    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    FORCE_OPTIONS = WaffleFlagCourseOverrideModel.ALL_CHOICES

    # Data format: ( is_enabled, force_choice, expected_result )
    @data((True, FORCE_OPTIONS.on, FORCE_OPTIONS.on),
          (True, FORCE_OPTIONS.off, FORCE_OPTIONS.off),
          (False, FORCE_OPTIONS.on, FORCE_OPTIONS.unset))
    @unpack
    def test_setting_flags_with_disabling(self, is_enabled, force_choice, expected_result):
        RequestCache.clear_request_cache()
        self.set_waffle_course_override(force_choice, is_enabled)
        override_value = WaffleFlagCourseOverrideModel.override_value(
            self.WAFFLE_TEST_NAME, self.TEST_COURSE_KEY
        )
        self.assertEqual(override_value, expected_result)

    def test_setting_flags_multiple_times(self):
        RequestCache.clear_request_cache()
        self.set_waffle_course_override(self.FORCE_OPTIONS.on)
        self.set_waffle_course_override(self.FORCE_OPTIONS.off)
        override_value = WaffleFlagCourseOverrideModel.override_value(
            self.WAFFLE_TEST_NAME, self.TEST_COURSE_KEY
        )
        self.assertEqual(override_value, self.FORCE_OPTIONS.off)

    def set_waffle_course_override(self, force_choice, is_enabled=True):
        WaffleFlagCourseOverrideModel.objects.create(
            waffle_flag=self.WAFFLE_TEST_NAME,
            force=force_choice,
            enabled=is_enabled,
            course_id=self.TEST_COURSE_KEY
        )
