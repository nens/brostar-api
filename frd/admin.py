from django.contrib import admin

from .models import FRD


class FRDAdmin(admin.ModelAdmin):
    model = FRD
    list_display = (
        "bro_id",
        "data_owner",
    )

    list_filter = ("data_owner",)


admin.site.register(FRD)
