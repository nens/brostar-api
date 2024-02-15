from django.contrib import admin
from django import forms
from . import models


class UserProfileAdminForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = "__all__"
        widgets = {
            "bro_user_token": forms.PasswordInput(render_value=True),
            "bro_user_password": forms.PasswordInput(render_value=True),
        }


class YourModelAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm


admin.site.register(models.UserProfile, YourModelAdmin)
admin.site.register(models.Organisation)
admin.site.register(models.ImportTask)
admin.site.register(models.UploadTask)
