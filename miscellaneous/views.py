import logging
import os
import tempfile

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from werkzeug.utils import secure_filename

from miscellaneous.utils.retrieve_gmw_duplicates import run as process_shapefile

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
ALLOWED_EXTENSIONS = {"zip", "shp", "shx", "dbf", "prj"}  # Shapefile components and zip


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def duplicates_index(request):
    """Main page view with upload form"""
    return render(request, "miscellaneous/duplicaat_index.html")


def process_shp(kvk_number: str, shp_file, shx_file):
    # Save both files
    tmp_dir = tempfile.mkdtemp()
    shp_filepath = os.path.join(tmp_dir, secure_filename(shp_file.name))
    shx_filepath = os.path.join(tmp_dir, secure_filename(shx_file.name))

    with open(shp_filepath, "wb+") as destination:
        for chunk in shp_file.chunks():
            destination.write(chunk)

    with open(shx_filepath, "wb+") as destination:
        for chunk in shx_file.chunks():
            destination.write(chunk)

    logger.info("Processing shapefile [SHP]")
    return process_shapefile(kvk_number=kvk_number, shapefile=shp_filepath)


def process_zip(kvk_number: str, zip_file) -> str:
    """Processes a ZIP file and returns the output CSV filename"""
    # Save zip
    tmp_dir = tempfile.mkdtemp()
    zip_filepath = os.path.join(tmp_dir, secure_filename(zip_file.name))

    with open(zip_filepath, "wb+") as destination:
        for chunk in zip_file.chunks():
            destination.write(chunk)

    logger.info("Processing shapefile [ZIP]")
    return process_shapefile(kvk_number=kvk_number, shapefile=zip_filepath)


def prepare_html(df: pd.DataFrame):
    # Convert delivery_accountable_party to string type
    df["delivery_accountable_party"] = df["delivery_accountable_party"].astype(str)

    # Drop unnecessary columns
    df = df.drop(
        columns=[
            "gm_gmw_pk",
            "latest_addition_time",
            "registration_completion_time",
            "latest_correction_time",
            "under_review_time",
            "deregistration_time",
            "imbro_xml_url",
            "local_vertical_reference_point",
            "object_registration_time",
            "construction_standard",
        ]
    )

    # Reorder columns
    df = df[
        [
            "well_code",
            "bro_id",
            "delivery_accountable_party",
            "owner",
            "number_of_monitoring_tubes",
            "well_construction_date",
            "well_removal_date",
            "ground_level_position",
            "coordinates",
            "nitg_code",
            "quality_regime",
            "well_head_protector",
            "initial_function",
        ]
    ]

    # Rename columns to Dutch
    df = df.rename(
        columns={
            "delivery_accountable_party": "Bronhouder",
            "number_of_monitoring_tubes": "Aantal buizen",
            "quality_regime": "Kwaliteitsregime",
            "well_code": "Putcode",
            "nitg_code": "NITG Code",
            "bro_id": "BRO ID",
            "coordinates": "Coordinated",
            "owner": "Eigenaar",
            "well_construction_date": "Inrichtings datum",
            "well_removal_date": "Verwijderings datum",
            "ground_level_position": "Maaiveldpositie",
            "well_head_protector": "Beschermconstructie",
            "initial_function": "Initiele functie",
        }
    )

    try:
        # Convert CSV to HTML for display
        csv_html = df.to_html(
            classes="table table-striped table-bordered table-hover",
            index=False,
            border=0,
        )
    except Exception as e:
        logger.info(f"Error processing files: {str(e)}")
        csv_html = None

    return csv_html


def duplicates_process(request):  # noqa: C901
    """Process uploaded shapefile and KVK number"""
    if request.method != "POST":
        return redirect("miscellaneous:duplicaat_index")

    # Check if KVK number is provided
    kvk_number = request.POST.get("kvk_number")
    if not kvk_number:
        messages.error(request, "KVK number is required")
        return redirect("miscellaneous:duplicaat_index")

    # Check if files were uploaded
    logger.info(f"KVK number: {kvk_number} and files: {request.FILES}")

    shp_file = request.FILES.get("shp_file")
    shx_file = request.FILES.get("shx_file")
    zip_file = request.FILES.get("zip_file")

    # If files were uploaded individually
    if shp_file and shx_file:
        if not (allowed_file(shp_file.name) and allowed_file(shx_file.name)):
            messages.error(request, "Invalid file types")
            return redirect("miscellaneous:duplicaat_index")
        filename = process_shp(kvk_number, shp_file, shx_file)
    elif zip_file:
        if not zip_file.name.endswith(".zip"):
            messages.error(request, "Please upload a .zip file")
            return redirect("miscellaneous:duplicaat_index")
        filename = process_zip(kvk_number, zip_file)
    else:
        messages.error(
            request,
            "Please upload either individual shapefile components or a zip file",
        )
        return redirect("miscellaneous:duplicaat_index")

    if filename is None:
        messages.error(request, "Geen features in de shapefile")
        return redirect("miscellaneous:duplicaat_index")

    csv_dir = settings.CSV_DIR
    df: pd.DataFrame = pd.read_csv(f"{csv_dir}/{filename}")

    csv_html = prepare_html(df)

    if csv_html is None:
        messages.error(request, "Error processing files")
        return redirect("miscellaneous:duplicaat_index")

    return render(
        request,
        "miscellaneous/result.html",
        {
            "csv_html": csv_html,
            "download_filename": filename,
        },
    )


def duplicates_download(request, filename):
    """Download the generated CSV file"""
    csv_dir = settings.CSV_DIR
    file = f"{csv_dir}/{filename}"
    return FileResponse(open(file, "rb"), as_attachment=True, filename=filename)


### Berichten hulp views
## General
def berichten_index(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_index.html")


def berichten_uitleg(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_uitleg.html")


## GMW
def berichten_gmw(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw.html")


def berichten_gmw_bestaand(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw2.html")


def berichten_gmw_gebeurtenissen(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw3.html")


def berichten_gmw_gebeurtenissen_peilbuis(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw3a.html")


def berichten_gmw_gebeurtenissen_filter(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw3b.html")


def berichten_gmw_gebeurtenissen_organisatie(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw3c.html")


def berichten_gmw_correctie(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmw4.html")


## GLD
def berichten_gld(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gld.html")


def berichten_gld_bestaand(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gld_bestaand.html")


## GMN
def berichten_gmn(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmn.html")


def berichten_gmn_bestaand(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gmn_bestaand.html")


## GAR
def berichten_gar(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gar.html")


def berichten_gar_bestaand(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_gar_bestaand.html")


## FRD
def berichten_frd(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_frd.html")


def berichten_frd_bestaand(request):
    """View for the berichten-hulp page"""
    return render(request, "miscellaneous/berichten_frd_bestaand.html")


def pricing(request):
    """View for the pricing page"""
    return render(request, "miscellaneous/pricing.html")
