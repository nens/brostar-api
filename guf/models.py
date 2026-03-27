import uuid

from django.db import models
from django.db.models import JSONField, Manager

from api.bro_upload.type_helpers import (
    DesignLoopTypeOptions,
    GUFDeliveryContextOptions,
    IndicationYesNoOptions,
    InstallationFunctionOptions,
    LegalTypeOptions,
    PubliclyAvailableOptions,
    QualityRegimeOptions,
    RelativeTemperatureOptions,
    UsageTypeOptions,
    WellFunctionOptions,
    literal_to_choices,
)


def is_usage_type_options(value) -> bool:
    if isinstance(value, list):
        return all(isinstance(item, str) and item in UsageTypeOptions for item in value)
    return value in UsageTypeOptions


def is_well_function_options(value) -> bool:
    if isinstance(value, list):
        return all(
            isinstance(item, str) and item in WellFunctionOptions for item in value
        )
    return value in WellFunctionOptions


class GUF(models.Model):
    """Ground Water Usage Facility

    The abbreviation GUF was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    internal_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Alleen beschikbaar voor de eigenaar van de put.",
    )
    bro_id = models.CharField(max_length=18)

    # BRO metadata fields
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(
        choices=literal_to_choices(QualityRegimeOptions), max_length=100, null=True
    )

    # StartRegistration sourcedocs_data fields
    delivery_context = models.CharField(
        choices=literal_to_choices(GUFDeliveryContextOptions),
        max_length=100,
        null=True,
        blank=True,
    )

    # License lifespan fields (variable granularity: date, yearMonth, or year)
    start_time = models.DateField(
        null=True, blank=True, help_text="Format: YYYY-MM-DD, YYYY-MM, or YYYY"
    )
    end_time = models.DateField(
        null=True, blank=True, help_text="Format: YYYY-MM-DD, YYYY-MM, or YYYY"
    )

    # License identification and legal information
    identification_licence = models.CharField(max_length=100, null=True, blank=True)
    legal_type = models.CharField(
        choices=literal_to_choices(LegalTypeOptions),
        max_length=100,
        null=True,
        blank=True,
    )

    # Usage type information
    primary_usage_type = models.CharField(
        choices=literal_to_choices(UsageTypeOptions),
        max_length=100,
        null=True,
        blank=True,
    )
    secondary_usage_types = JSONField(
        "Secondary Usage Types",
        default=list,
        blank=True,
        validators=[is_usage_type_options],
    )  # Each row has to be of UsageTypeOptions
    human_consumption = models.CharField(
        choices=literal_to_choices(IndicationYesNoOptions),
        max_length=100,
        null=True,
        blank=True,
    )

    # Licensed quantities (reused at license and installation levels)
    licensed_quantities = JSONField("Licensed Quantities", default=list, blank=True)

    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    # Related managers
    installations = Manager["DesignInstallation"]
    events = Manager["GUFEvent"]

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "GUF's"

    @property
    def nr_of_installations(self) -> int:
        return self.installations.count()

    @property
    def nr_of_events(self) -> int:
        return self.events.count()


class DesignInstallation(models.Model):
    """A design installation is part of a GUF license."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guf = models.ForeignKey(
        GUF, on_delete=models.CASCADE, null=False, related_name="installations"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )

    # Design installation identification
    design_installation_id = models.CharField(max_length=100, null=True, blank=True)
    installation_function = models.CharField(
        choices=literal_to_choices(InstallationFunctionOptions),
        max_length=100,
        null=True,
        blank=True,
    )

    # Geometry (Point coordinates as string for XML compatibility)
    design_installation_pos = models.CharField(
        max_length=200, null=True, blank=True, help_text="Point coordinates as string"
    )

    # Licensed quantities at installation level
    licensed_quantities = JSONField("Licensed Quantities", default=list, blank=True)

    # Related managers
    loops = Manager["DesignLoop"]
    wells = Manager["DesignWell"]
    surface_infiltrations = Manager["DesignSurfaceInfiltration"]

    def __str__(self) -> str:
        return f"{self.guf}-{self.design_installation_id}"

    class Meta:
        verbose_name_plural = "Design Installations"

    @property
    def nr_of_loops(self) -> int:
        return self.loops.count()

    @property
    def nr_of_wells(self) -> int:
        return self.wells.count()

    @property
    def nr_of_surface_infiltrations(self) -> int:
        return self.surface_infiltrations.count()


class EnergyCharacteristics(models.Model):
    """Energy characteristics of a design installation, applicable for energy systems."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation = models.OneToOneField(
        DesignInstallation,
        on_delete=models.CASCADE,
        null=False,
        related_name="energy_characteristics",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    energy_cold = models.CharField(max_length=100, null=True, blank=True)
    energy_warm = models.CharField(max_length=100, null=True, blank=True)

    maximum_infiltration_temperature_warm = models.CharField(
        max_length=100, null=True, blank=True
    )
    average_infiltration_temperature_cold = models.CharField(
        max_length=100, null=True, blank=True
    )
    average_infiltration_temperature_warm = models.CharField(
        max_length=100, null=True, blank=True
    )

    power_cold = models.CharField(max_length=100, null=True, blank=True)
    power_warm = models.CharField(max_length=100, null=True, blank=True)
    power = models.CharField(max_length=100, null=True, blank=True)

    average_warm_water = models.CharField(max_length=100, null=True, blank=True)
    average_cold_water = models.CharField(max_length=100, null=True, blank=True)
    maximum_year_quantity_warm = models.CharField(max_length=100, null=True, blank=True)
    maximum_year_quantity_cold = models.CharField(max_length=100, null=True, blank=True)

    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )


class DesignLoop(models.Model):
    """A design loop is part of a design installation."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation = models.ForeignKey(
        DesignInstallation, on_delete=models.CASCADE, null=False, related_name="loops"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )

    # Design loop identification
    design_loop_id = models.CharField(max_length=100, null=True, blank=True)
    loop_type = models.CharField(
        choices=literal_to_choices(DesignLoopTypeOptions),
        max_length=100,
        null=True,
        blank=True,
    )

    # Lifespan (variable granularity: date, yearMonth, or year)
    start_date = models.DateField(
        null=True, blank=True, help_text="Format: YYYY-MM-DD, YYYY-MM, or YYYY"
    )
    end_date = models.DateField(
        null=True, blank=True, help_text="Format: YYYY-MM-DD, YYYY-MM, or YYYY"
    )

    # Geometry (Point or LineString)
    geometry_type = models.CharField(
        max_length=50, null=True, blank=True, help_text="Point or LineString"
    )
    design_loop_pos = models.TextField(
        null=True, blank=True, help_text="Geometry coordinates as string"
    )

    def __str__(self) -> str:
        return f"{self.installation}-{self.design_loop_id}"

    class Meta:
        verbose_name_plural = "Design Loops"


class DesignWell(models.Model):
    """A design well is part of a design installation."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation = models.ForeignKey(
        DesignInstallation, on_delete=models.CASCADE, null=False, related_name="wells"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )

    # Design well identification
    design_well_id = models.CharField(max_length=100, null=True, blank=True)

    # Well functions (array of strings)
    well_functions = JSONField(
        "Well Functions",
        default=list,
        blank=True,
        validators=[is_well_function_options],
    )  # Each row has to be of WellFunctionOptions

    # Physical characteristics
    height = models.CharField(max_length=50, null=True, blank=True)
    well_pos = models.CharField(
        max_length=200, null=True, blank=True, help_text="Point coordinates as string"
    )
    geometry_publicly_available = models.CharField(
        choices=literal_to_choices(PubliclyAvailableOptions),
        max_length=100,
        null=True,
        blank=True,
    )

    # Optional depth and capacity
    maximum_well_depth = models.CharField(max_length=50, null=True, blank=True)
    maximum_well_depth_publicly_available = models.CharField(
        choices=literal_to_choices(PubliclyAvailableOptions),
        max_length=100,
        null=True,
        blank=True,
    )
    maximum_well_capacity = models.CharField(max_length=50, null=True, blank=True)

    # Conditional temperature (for certain installation functions)
    relative_temperature = models.CharField(
        choices=literal_to_choices(RelativeTemperatureOptions),
        max_length=50,
        null=True,
        blank=True,
    )

    # Design screen (nested object: screenType, designScreenTop, designScreenBottom)
    design_screen = JSONField("Design Screen", default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.installation}-{self.design_well_id}"

    class Meta:
        verbose_name_plural = "Design Wells"


class DesignSurfaceInfiltration(models.Model):
    """A design surface infiltration is part of a design installation."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation = models.ForeignKey(
        DesignInstallation,
        on_delete=models.CASCADE,
        null=False,
        related_name="surface_infiltrations",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )

    # Design surface infiltration identification
    design_surface_infiltration_id = models.CharField(
        max_length=100, null=True, blank=True
    )

    # Geometry (Polygon coordinates as string)
    design_surface_infiltration_pos = models.TextField(
        null=True, blank=True, help_text="Polygon coordinates as string"
    )

    def __str__(self) -> str:
        return f"{self.installation}-{self.design_surface_infiltration_id}"

    class Meta:
        verbose_name_plural = "Design Surface Infiltrations"


class GUFEvent(models.Model):
    """A GUF event is a change after a period of time to a GUF or its installations."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    guf = models.ForeignKey(
        GUF, on_delete=models.CASCADE, null=False, related_name="events"
    )
    event_name = models.CharField(
        max_length=40,
        help_text="Event type: Height, NewLicense, WellFunction, Closure, etc.",
    )
    event_date = models.DateField()
    metadata = JSONField("Metadata", default=dict, blank=False)
    sourcedocument_data = JSONField("Sourcedocument data", default=dict, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.guf}-{self.event_name}-{self.event_date}"

    class Meta:
        verbose_name_plural = "GUF Events"
