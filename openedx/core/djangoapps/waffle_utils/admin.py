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
            'fields': ('course_id', 'waffle_flag', 'enabled'),
            'description': 'Enter a valid course id and an existing waffle flag. If they are invalid, an error message will display.'
        }),
    )

admin.site.register(CourseOverrideWaffleFlagModel, CourseOverrideWaffleFlagAdmin)
