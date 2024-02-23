from . import object_import

object_importer_mapping = {
    "GMN": object_import.GMNObjectImporter,
    "GMW": object_import.GMWObjectImporter,
    "GLD": object_import.GLDObjectImporter,
    "FRD": object_import.FRDObjectImporter,
}
