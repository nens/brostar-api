from django import forms
from django.contrib import admin

from . import models as api_models


class UserProfileAdminForm(forms.ModelForm):
    class Meta:
        model = api_models.UserProfile
        fields = "__all__"
        widgets = {
            "bro_user_token": forms.PasswordInput(render_value=True),
            "bro_user_password": forms.PasswordInput(render_value=True),
        }


class YourModelAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm


admin.site.register(api_models.UserProfile, YourModelAdmin)
admin.site.register(api_models.Organisation)
admin.site.register(api_models.ImportTask)
admin.site.register(api_models.UploadTask)
