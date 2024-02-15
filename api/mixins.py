from rest_framework.reverse import reverse


class UrlFieldMixin:
    """
    Mixin to add a URL field to serialized data.
    """

    def get_url_field(self, obj):
        """
        Method to get the URL field.
        """
        request = self.context.get("request")
        if request and obj:
            app_name = obj._meta.app_label
            if app_name != "api":
                app_name = f"api:{app_name}"

            model_name = obj._meta.model_name
            return reverse(
                f"{app_name}:{model_name}-detail",
                kwargs={"uuid": obj.uuid},
                request=request,
                format=None,
            )
        return None

    def to_representation(self, instance):
        """
        Method to include the URL field in serialized data.
        """
        data = super().to_representation(instance)
        url_field = self.get_url_field(instance)  # Get the URL field using the mixin
        if url_field:
            data = {"url": url_field, **data}  # Add URL field at the top
        return data
