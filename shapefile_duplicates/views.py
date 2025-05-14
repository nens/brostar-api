import datetime
import logging
import os

import pandas as pd
from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from werkzeug.utils import secure_filename

import shapefile_duplicates
from shapefile_duplicates.utils.retrieve_gmw_duplicates import run as process_shapefile

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
pth = os.path.dirname(shapefile_duplicates.__file__)
UPLOAD_FOLDER = os.path.join(pth, "uploads")
ALLOWED_EXTENSIONS = {"zip", "shp", "shx", "dbf", "prj"}  # Shapefile components and zip

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def index(request):
    """Main page view with upload form"""
    return render(request, "shapefile_duplicates/index.html")


def process_shp(kvk_number: str, shp_file, shx_file):
    # Save both files
    shp_filepath = os.path.join(UPLOAD_FOLDER, secure_filename(shp_file.name))
    shx_filepath = os.path.join(UPLOAD_FOLDER, secure_filename(shx_file.name))

    with open(shp_filepath, "wb+") as destination:
        for chunk in shp_file.chunks():
            destination.write(chunk)

    with open(shx_filepath, "wb+") as destination:
        for chunk in shx_file.chunks():
            destination.write(chunk)

    logger.info("Processing shapefile [SHP]")
    process_shapefile(kvk_number=kvk_number, shapefile=shp_filepath)


def process_zip(kvk_number: str, zip_file):
    # Save zip
    zip_filepath = os.path.join(UPLOAD_FOLDER, secure_filename(zip_file.name))

    with open(zip_filepath, "wb+") as destination:
        for chunk in zip_file.chunks():
            destination.write(chunk)

    logger.info("Processing shapefile [ZIP]")
    process_shapefile(kvk_number=kvk_number, shapefile=zip_filepath)


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
        logger.exception(f"Error processing files: {str(e)}")
        csv_html = None

    return csv_html


def process(request):  # noqa: C901
    """Process uploaded shapefile and KVK number"""
    if request.method != "POST":
        return redirect("shapefile_duplicates:index")

    # Check if KVK number is provided
    kvk_number = request.POST.get("kvk_number")
    if not kvk_number:
        messages.error(request, "KVK number is required")
        return redirect("shapefile_duplicates:index")

    # Check if files were uploaded
    logger.info(f"KVK number: {kvk_number} and files: {request.FILES}")

    shp_file = request.FILES.get("shp_file")
    shx_file = request.FILES.get("shx_file")
    zip_file = request.FILES.get("zip_file")

    # If files were uploaded individually
    if shp_file and shx_file:
        if not (allowed_file(shp_file.name) and allowed_file(shx_file.name)):
            messages.error(request, "Invalid file types")
            return redirect("shapefile_duplicates:index")
        process_shp(kvk_number, shp_file, shx_file)
    elif zip_file:
        if not zip_file.name.endswith(".zip"):
            messages.error(request, "Please upload a .zip file")
            return redirect("shapefile_duplicates:index")
        process_zip(kvk_number, zip_file)
    else:
        messages.error(
            request,
            "Please upload either individual shapefile components or a zip file",
        )
        return redirect("shapefile_duplicates:index")

    # Read the CSV output generated by the utility function
    date = datetime.datetime.now().strftime("%Y%m%d")
    csv_filename = f"result_{date}_{kvk_number}.csv"
    csv_filepath = os.path.join(UPLOAD_FOLDER, csv_filename)

    df: pd.DataFrame = pd.read_csv(csv_filepath)

    csv_html = prepare_html(df)

    if csv_html is None:
        messages.error(request, "Error processing files")
        return redirect("shapefile_duplicates:index")

    return render(
        request,
        "shapefile_duplicates/result.html",
        {
            "csv_html": csv_html,
            "download_filename": csv_filename,
        },
    )


def download_file(request, filename):
    """Download the generated CSV file"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return FileResponse(open(filepath, "rb"), as_attachment=True, filename=filename)
