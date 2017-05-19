"""
Models for configuring waffle utils.
"""
from django.db.models import CharField
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from config_models.models import ConfigurationModel
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from request_cache.middleware import request_cached


class CourseOverrideWaffleFlagModel(ConfigurationModel):
    """
    Used to force a waffle flag on or off for a course.
    """
    FORCE_CHOICES = Choices(('on', _('Force On')), ('off', _('Force Off')))
    ALL_CHOICES = FORCE_CHOICES + Choices('unset')

    KEY_FIELDS = ('waffle_flag', 'course_id')

    # The course that these features are attached to.
    waffle_flag = CharField(max_length=255, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    force = CharField(choices=FORCE_CHOICES, default=FORCE_CHOICES.on, max_length=3)

    @classmethod
    @request_cached
    def override_value(cls, waffle_flag, course_id):
        """
        Returns whether the waffle flag was overridden (on or off) for the
        course, or is unset.

        Arguments:
            waffle_flag (String): The name of the flag.
            course_id (CourseLocator): The course id for which the flag may have
                been overridden.

        If the current config is not set or disabled for this waffle flag and
            course id, returns ALL_CHOICES.unset.
        Otherwise, returns ALL_CHOICES.on or ALL_CHOICES.off as configured for
            the force option.

        """
        if not course_id or not waffle_flag:
            return cls.ALL_CHOICES.unset

        effective = cls.objects.filter(waffle_flag=waffle_flag, course_id=course_id).order_by('-change_date').first()
        if effective and effective.enabled:
            return effective.force
        return cls.ALL_CHOICES.unset

    class Meta(object):
        app_label = "waffle_utils"

    def __unicode__(self):
        enabled_label = "Enabled" if self.enabled else "Not Enabled"
        # pylint: disable=no-member
        return u"Course '{}': Persistent Grades {}".format(self.course_id.to_deprecated_string(), enabled_label)
