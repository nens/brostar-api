import logging

from django import forms
from django.conf import settings
from django.contrib import admin
from nens_auth_client.models import Invitation
from rest_framework_api_key.admin import APIKeyModelAdmin
from rest_framework_api_key.models import APIKey

from . import models as api_models

admin.site.unregister(APIKey)  # unused model

logger = logging.getLogger(__name__)


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
    list_display = (
        "name",
        "request_count",
    )


class ContractAdmin(admin.ModelAdmin):
    model = api_models.Contract
    list_display = (
        "organisation",
        "start_date",
        "nr_of_messages",
    )


class InviteUserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "organisation",
        "invitation_status",
        "created",
        "updated",
    )

    def save_model(self, request, obj, form, change):
        """
        Override save_model to create an Invitation when a new InviteUser is created.
        """
        super().save_model(request, obj, form, change)

        if not change:
            invitation = Invitation.objects.create(email=obj.email)

            if not settings.DEBUG:
                invitation.send_email(
                    request=request,
                    context={
                        "invitation_language": "nl",
                    },
                )
            else:
                logger.debug("No mails are sent in development mode.")

            obj.nens_auth_client_invitation = invitation
            obj.save()

    def invitation_status(self, obj):
        return obj.get_status()


class UploadTaskAdmin(admin.ModelAdmin):
    model = api_models.UploadTask
    list_display = (
        "bro_id",
        "request_type",
        "registration_type",
        "status",
        "data_owner",
    )

    list_filter = ("data_owner", "bro_id")


class BulkUploadAdmin(admin.ModelAdmin):
    model = api_models.BulkUpload
    list_display = (
        "bulk_upload_type",
        "request_type",
        "status",
        "data_owner",
    )

    list_filter = ("data_owner", "bulk_upload_type")


admin.site.register(api_models.UserProfile)
admin.site.register(api_models.InviteUser, InviteUserAdmin)
admin.site.register(api_models.Organisation, OrganisationAdmin)
admin.site.register(api_models.ImportTask)
admin.site.register(api_models.UploadTask, UploadTaskAdmin)
admin.site.register(api_models.BulkUpload, BulkUploadAdmin)
admin.site.register(api_models.UploadFile)
