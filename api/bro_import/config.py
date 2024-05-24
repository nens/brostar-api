from . import object_import

object_importer_mapping = {
    "GMN": object_import.GMNObjectImporter,
    "GMW": object_import.GMWObjectImporter,
    "GAR": object_import.GARObjectImporter,
    "GLD": object_import.GLDObjectImporter,
}
