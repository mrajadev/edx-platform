"""
Django admin page for waffle utils models
"""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin


from .forms import CourseOverrideWaffleFlagAdminForm
from .models import CourseOverrideWaffleFlagModel


class CourseOverrideWaffleFlagAdmin(KeyedConfigurationModelAdmin):
    """
    Admin for course override of waffle flags.

    Includes search by course_id and waffle_flag.

    """
    form = CourseOverrideWaffleFlagAdminForm
    search_fields = ['course_id', 'waffle_flag']
    fieldsets = (
        (None, {
            'fields': ('course_id', 'waffle_flag', 'force', 'enabled'),
            'description': 'Enter a valid course id and an existing waffle flag. The waffle flag name is not validated.'
        }),
    )

admin.site.register(CourseOverrideWaffleFlagModel, CourseOverrideWaffleFlagAdmin)
