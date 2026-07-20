import datetime
import logging

from pyproj import Transformer

logger = logging.getLogger(__name__)

# Define transformer from RD New (EPSG:28992) to ETRS89 (EPSG:4258 = lat/lon)
transformer = Transformer.from_crs("EPSG:28992", "EPSG:4258", always_xy=True)


def empty_strings_to_none(d: dict) -> dict:
    for key, value in d.items():
        if isinstance(value, str) and value.strip() == "":
            d[key] = None
        elif isinstance(value, dict):
            d[key] = empty_strings_to_none(value)
        elif isinstance(value, list):
            d[key] = [
                empty_strings_to_none(v)
                if isinstance(v, dict)
                else (None if v == "" else v)
                for v in value
            ]
    return d


def strip_whitespace(data):
    if isinstance(data, dict):
        return {k: strip_whitespace(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [strip_whitespace(item) for item in data]
    elif isinstance(data, str):
        return data.strip()
    return data


def drop_empty_strings(d: dict) -> dict:  # noqa: C901
    cleaned = {}
    for key, value in d.items():
        if isinstance(value, str):
            if value.strip() == "":
                continue  # skip this field entirely
            cleaned[key] = value
        elif isinstance(value, dict):
            nested = drop_empty_strings(value)
            if nested:  # only keep if not empty
                cleaned[key] = nested
        elif isinstance(value, list):
            cleaned_list = []
            for v in value:
                if isinstance(v, dict):
                    nested = drop_empty_strings(v)
                    if nested:
                        cleaned_list.append(nested)
                elif not (isinstance(v, str) and v.strip() == ""):
                    cleaned_list.append(v)
            if cleaned_list:
                cleaned[key] = cleaned_list
        else:
            cleaned[key] = value
    return cleaned


def parse_flexible_date(date_str: str | None) -> datetime.date | None:
    """Parse BRO dates with flexible granularity: YYYY-MM-DD, YYYY-MM, or YYYY."""
    if not date_str:
        return None
    try:
        if len(date_str) == 4:  # YYYY
            return datetime.date(int(date_str), 1, 1)
        elif len(date_str) == 7:  # YYYY-MM
            year, month = date_str.split("-")
            return datetime.date(int(year), int(month), 1)
        else:  # YYYY-MM-DD
            return datetime.date.fromisoformat(date_str)
    except (ValueError, AttributeError):
        return None
