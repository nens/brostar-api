from django import forms
from django.contrib import admin

from . import models as api_models


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


admin.site.register(api_models.UserProfile)
admin.site.register(api_models.Organisation, OrganisationAdmin)
admin.site.register(api_models.ImportTask)
admin.site.register(api_models.UploadTask)
