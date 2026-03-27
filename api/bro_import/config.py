from . import object_import

object_importer_mapping: dict[str, type[object_import.ObjectImporter]] = {
    "GMN": object_import.GMNObjectImporter,
    "GMW": object_import.GMWObjectImporter,
    "GAR": object_import.GARObjectImporter,
    "GLD": object_import.GLDObjectImporter,
    "FRD": object_import.FRDObjectImporter,
    "GUF": object_import.GUFObjectImporter,
    "GPD": object_import.GPDObjectImporter,
}
