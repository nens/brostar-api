from django import forms
from django.contrib import admin
from rest_framework_api_key.admin import APIKeyModelAdmin
from rest_framework_api_key.models import APIKey

from . import models as api_models

admin.site.unregister(APIKey)  # unused model


@admin.register(api_models.PersonalAPIKey)
class PersonalAPIKeyAdmin(APIKeyModelAdmin):
    list_display = ("user", "name", "prefix", "last_used", "scope")
    list_select_related = ("user",)
    search_fields = ("user__username", "name", "prefix")
    raw_id_fields = ("user",)
    list_filter = ("last_used", "created", "user")

    def get_readonly_fields(self, request, obj):
        """first get the readonly fields from the base class,
        then append our own fields.
        """
        readonly_fields = ("last_used",)
        return super().get_readonly_fields(request, obj) + readonly_fields


class OrganisationAdminForm(forms.ModelForm):
    class Meta:
        model = api_models.Organisation
        fields = "__all__"
        widgets = {
            "bro_user_token": forms.PasswordInput(render_value=True),
            "bro_user_password": forms.PasswordInput(render_value=True),
        }


class OrganisationAdmin(admin.ModelAdmin):
    form = OrganisationAdminForm


class InviteUserAdmin(admin.ModelAdmin):
    list_display = ("email", "organisation", "invitation_status", "created", "updated")

    def invitation_status(self, obj):
        return obj.get_status()


admin.site.register(api_models.UserProfile)
admin.site.register(api_models.InviteUser, InviteUserAdmin)
admin.site.register(api_models.Organisation, OrganisationAdmin)
admin.site.register(api_models.ImportTask)
admin.site.register(api_models.UploadTask)
admin.site.register(api_models.BulkUpload)
admin.site.register(api_models.UploadFile)
