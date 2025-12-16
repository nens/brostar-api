import io
import zipfile
from unittest import mock

import polars as pl
import pytest
import requests
from django.core.files.uploadedfile import SimpleUploadedFile

from api.bro_upload.utils import (
    T,
    add_xml_to_upload,
    check_delivery_status,
    create_delivery,
    create_upload_url,
    detect_delimiter_from_content,
    file_to_df,
    include_delivery_responsible_party,
    read_csv,
    read_zip,
    simplify_validation_errors,
    validate_xml_file,
)
from api.models import Organisation, UploadFile
from api.tests.fixtures import bulk_upload, organisation

organisation
bulk_upload
T


# Test simplify_validation_errors function
def test_simplify_validation_errors():
    errors = [
        {
            "loc": ("recursive_model", "lng"),
            "msg": "Field1 is required",
            "type": "value_error.missing",
        },
        {
            "loc": ("field2",),
            "msg": "Field2 must be a string",
            "type": "type_error.str",
        },
    ]

    simplified = simplify_validation_errors(errors)

    assert simplified == {
        "recursive_model - lng": "Field1 is required",
        "field2": "Field2 must be a string",
    }


def test_detect_delimiter_from_content_error():
    # Should raise an csv.Error and return komma as default
    delimiter = detect_delimiter_from_content(12345)  # Invalid input type
    assert delimiter == ","


# Mocking external API responses for the functions involving requests
@pytest.fixture
def mock_requests():
    with (
        mock.patch("requests.post") as mock_post,
        mock.patch("requests.get") as mock_get,
    ):
        yield mock_post, mock_get


# Test validate_xml_file function (mocked)
# Test validate_xml_file function (mocked)
def test_validate_xml_file_success():
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"status": "VALID"}
        mock_response.raise_for_status = mock.Mock()  # does nothing
        mock_post.return_value = mock_response

        result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
        assert result == {"status": "VALID"}


def test_validate_xml_file_server_error():
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "API failure"
        )
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
        assert result["status"] == "NIET-VALIDE"
        assert "BRO API is momenteel niet beschikbaar" in str(result["errors"])


def test_validate_xml_file_unauthorized():
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Auth failure"
        )
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
        assert result["status"] == "NIET-VALIDE"
        assert "niet gemachtigd" in str(result["errors"])


def test_validate_xml_file_forbidden():
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Forbidden"
        )
        mock_response.status_code = 403
        mock_post.return_value = mock_response

        result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
        assert result["status"] == "NIET-VALIDE"
        assert "niet de juiste rechten" in str(result["errors"])


def test_validate_xml_file_unhandled_http_error():
    """Test default case (_) - unhandled HTTP status code"""
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Unexpected error"
        )
        mock_response.status_code = 418  # I'm a teapot (or any unhandled status)
        mock_post.return_value = mock_response

        result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
        assert result["status"] == "NIET-VALIDE"
        assert "Er is een fout opgetreden bij het valideren" in str(result["errors"])
        assert "Unexpected error" in str(result["errors"])


def test_validate_xml_file_generic_exception():
    """Test generic Exception handler (not HTTPError)"""
    with mock.patch("requests.Session.post") as mock_post:
        mock_post.side_effect = ValueError("Something went wrong with the request")

        result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
        assert result["status"] == "NIET-VALIDE"
        assert "Er is een fout opgetreden bij het valideren" in str(result["errors"])
        assert "Something went wrong with the request" in str(result["errors"])


# Test create_upload_url function (mocked)
def test_create_upload_url_success():
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.headers = {
            "Location": "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads"
        }
        mock_response.raise_for_status = mock.Mock()
        mock_post.return_value = mock_response

        project_number = "1234"
        result = create_upload_url("bro_user", "bro_pass", project_number)
        assert result["status"] == "OK"
        assert (
            result["upload_url"]
            == "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads"
        )


def test_create_upload_url_http_error():
    """Test generic HTTPError without specific status code"""
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "API failure"
        )
        mock_post.return_value = mock_response

        project_number = "12345"
        result = create_upload_url("bro_user", "bro_pass", project_number)
        assert result["status"] == "NIET-VALIDE"
        assert result["errors"] == ["Error: API failure."]


def test_create_upload_url_unauthorized():
    """Test 401 Unauthorized error"""
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Authentication failure"
        )
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        project_number = "12345"
        result = create_upload_url("bro_user", "bro_pass", project_number)
        assert result["status"] == "NIET-VALIDE"
        assert result["errors"] == [
            f"Het gebruikte token is niet gemachtigd voor project {project_number}"
        ]


def test_create_upload_url_generic_exception():
    """Test generic Exception handler (not HTTPError)"""
    with mock.patch("requests.Session.post") as mock_post:
        mock_post.side_effect = ValueError("Connection error or other issue")

        project_number = "12345"
        result = create_upload_url("bro_user", "bro_pass", project_number)
        assert result["status"] == "NIET-VALIDE"
        # errors: f"Er is een fout opgetreden bij het aanmaken van de upload: {e}."
        assert len(result["errors"]) == 1
        assert (
            "Er is een fout opgetreden bij het aanmaken van de upload"
            in result["errors"][0]
        )


# Test add_xml_to_upload function (mocked)
def test_add_xml_to_upload():
    with mock.patch("requests.Session.post") as mock_post:
        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.headers = {
            "Location": "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/"
        }
        mock_response.raise_for_status = mock.Mock()
        mock_post.return_value = mock_response

        result = add_xml_to_upload(
            "<xml>data</xml>",
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads",
            "bro_user",
            "bro_pass",
        )
        assert result == "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/"

        # Test request failure
        mock_post.side_effect = requests.exceptions.RequestException("API failure")
        result = add_xml_to_upload(
            "<xml>data</xml>",
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads",
            "bro_user",
            "bro_pass",
        )
        assert result is None


# Test create_delivery function (mocked)
def test_create_delivery():
    with mock.patch("requests.Session.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.headers = {
            "Location": "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen"
        }
        mock_response.raise_for_status = mock.Mock()
        mock_post.return_value = mock_response

        result = create_delivery(
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/0000013524",
            "bro_user",
            "bro_pass",
            "1234",
        )
        assert result == "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen"

        # Test request failure
        mock_post.side_effect = requests.exceptions.RequestException("API failure")
        result = create_delivery(
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/0000013524",
            "bro_user",
            "bro_pass",
            "1234",
        )
        assert result is None


# Test check_delivery_status function (mocked)
def test_check_delivery_status():
    with mock.patch("requests.Session.get") as mock_get:
        # Mock successful API response
        mock_response = mock.Mock()
        mock_response.json.return_value = {"status": "delivered"}
        mock_get.return_value = mock_response

        result = check_delivery_status(
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen",
            "bro_user",
            "bro_pass",
        )
        assert result == {"status": "delivered"}

        # Test request failure
        mock_get.side_effect = requests.exceptions.RequestException("API failure")
        result = check_delivery_status(
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen",
            "bro_user",
            "bro_pass",
        )
        assert result is None


# Test include_delivery_responsible_party function
@pytest.mark.django_db
def test_include_delivery_responsible_party():
    import uuid

    _uuid = uuid.uuid4()
    # Simulate an existing Organisation
    Organisation.objects.create(uuid=_uuid, kvk_number="12345678")

    # Test when data_owner is the same as kvk_number
    result = include_delivery_responsible_party("12345678", str(_uuid))
    assert not result  # Responsible party is not included

    # Test when data_owner is different
    result = include_delivery_responsible_party("87654321", str(_uuid))
    assert result  # Responsible party should be included

    # Test when data_owner is None
    result = include_delivery_responsible_party("87654321", None)
    assert result  # Responsible party should be included when no data_owner

    result = include_delivery_responsible_party(None, str(_uuid))
    assert not result


@pytest.mark.django_db
def test_read_csv_from_uploadfile(bulk_upload):
    file = SimpleUploadedFile(
        "data.csv", b"name,age\nAlice,30\nBob,25", content_type="text/csv"
    )
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)
    df = read_csv(upload)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 2)
    assert df.columns == ["name", "age"]


@pytest.mark.django_db
def test_read_csv_from_bytes():
    df = read_csv(b"name,age\nAlice,30\nBob,25")
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 2)


@pytest.mark.django_db
def test_read_csv_from_filepath():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=True) as tmp:
        tmp.write("name,age\nAlice,30\nBob,25")
        tmp.flush()
        df = read_csv(tmp.name)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 2)


@pytest.mark.django_db
def test_read_csv_invalid():
    with pytest.raises(TypeError, match="Unsupported file type passed to read_csv."):
        read_csv(12345)  # Invalid type


@pytest.mark.django_db
def test_read_zip_with_no_valid_files(monkeypatch, bulk_upload):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("readme.txt", b"This is a readme file.")
        zip_file.writestr("image.png", b"\x89PNG\r\n\x1a\n")

    buffer.seek(0)
    file = SimpleUploadedFile(
        "archive.zip", buffer.read(), content_type="application/zip"
    )
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)

    with pytest.raises(
        ValueError, match="No CSV and no Excel files found in the zip archive."
    ):
        read_zip(upload)


@pytest.mark.django_db
def test_read_zip_with_csv_and_excel(monkeypatch, bulk_upload):
    csv_data = b"name,age\nAlice,30"
    fake_excel_data = b"dummy content"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("test.csv", csv_data)
        zip_file.writestr("sheet.xlsx", fake_excel_data)
        zip_file.writestr("sheet.xls", fake_excel_data)

    buffer.seek(0)
    file = SimpleUploadedFile(
        "archive.zip", buffer.read(), content_type="application/zip"
    )
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)

    monkeypatch.setattr(
        "api.bro_upload.utils.read_csv", lambda f: pl.DataFrame({"measurement": [1]})
    )
    monkeypatch.setattr(
        "api.bro_upload.utils.read_excel",
        lambda source: pl.DataFrame({"measurement": [99]}),
    )

    df = read_zip(upload)
    assert isinstance(df, pl.DataFrame)
    assert "measurement" in df.columns
    items = [1, 99]
    for item in items:
        assert item in df.select("measurement").to_series(0).to_list()


@pytest.mark.django_db
def test_file_to_df_csv(bulk_upload):
    file = SimpleUploadedFile("data.csv", b"a,b\n1,2\n3,4", content_type="text/csv")
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)
    df = file_to_df(upload)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 2)


@pytest.mark.django_db
def test_file_to_df_excel(monkeypatch, bulk_upload):
    monkeypatch.setattr(
        "api.bro_upload.utils.read_excel", lambda source: pl.DataFrame({"col": [123]})
    )
    file = SimpleUploadedFile(
        "sheet.xlsx", b"excel content", content_type="application/vnd.ms-excel"
    )
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)
    df = file_to_df(upload)
    assert isinstance(df, pl.DataFrame)
    assert df.shape[0] == 1


@pytest.mark.django_db
def test_file_to_df_zip(monkeypatch, bulk_upload):
    csv_data = b"a,b\n5,6"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        zip_file.writestr("data.csv", csv_data)
    buffer.seek(0)

    file = SimpleUploadedFile(
        "archive.zip", buffer.read(), content_type="application/zip"
    )
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)

    monkeypatch.setattr(
        "api.bro_upload.utils.read_zip",
        lambda upload: pl.DataFrame({"a": [5], "b": [6]}),
    )

    df = file_to_df(upload)
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (1, 2)


@pytest.mark.django_db
def test_file_to_df_invalid_extension(bulk_upload):
    file = SimpleUploadedFile("note.txt", b"not a csv", content_type="text/plain")
    upload = UploadFile.objects.create(bulk_upload=bulk_upload, file=file)
    with pytest.raises(ValueError, match="Unsupported file type"):
        file_to_df(upload)


### For read Excel, but needs xlsxwriter dependency which is not yet added
# class MockUploadFile:
#     """Mock UploadFile class for testing"""
#     def __init__(self, file_path: str):
#         self.file = Mock()
#         self.file.path = file_path


# def create_test_excel_file() -> tuple[Path, pl.DataFrame]:
#     """Helper function to create a test Excel file"""
#     # Create test data
#     test_data = pl.DataFrame({
#         "name": ["Alice", "Bob", "Charlie"],
#         "age": [25, 30, 35],
#         "city": ["New York", "London", "Paris"]
#     })

#     # Create temporary file
#     temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
#     temp_path = Path(temp_file.name)
#     temp_file.close()

#     # Write test data to Excel
#     test_data.write_excel(temp_path)

#     return temp_path, test_data


# class TestReadExcel:
#     """Test suite for read_excel function"""

#     @pytest.fixture
#     def excel_file_path(self):
#         """Fixture that creates and cleans up a test Excel file"""
#         temp_path, test_data = create_test_excel_file()
#         yield temp_path, test_data
#         # Cleanup
#         temp_path.unlink(missing_ok=True)

#     def test_read_excel_with_upload_file(self, excel_file_path):
#         """Test read_excel with UploadFile object"""
#         temp_path, expected_data = excel_file_path

#         # Create mock UploadFile
#         upload_file = MockUploadFile(str(temp_path))

#         result = read_excel(upload_file)

#         # Assertions
#         assert isinstance(result, pl.DataFrame)
#         assert result.shape == expected_data.shape
#         assert result.columns == expected_data.columns
#         assert result.equals(expected_data)

#     def test_read_excel_with_bytes(self, excel_file_path):
#         """Test read_excel with bytes object"""
#         temp_path, expected_data = excel_file_path

#         # Read file as bytes
#         with open(temp_path, 'rb') as f:
#             file_bytes = f.read()

#         # Replace with your actual function import
#         result = read_excel(file_bytes)

#         # Assertions
#         assert isinstance(result, pl.DataFrame)
#         assert result.shape == expected_data.shape
#         assert result.columns == expected_data.columns
#         assert result.equals(expected_data)

#     def test_read_excel_with_bytesio(self, excel_file_path):
#         """Test read_excel with BytesIO object"""
#         temp_path, expected_data = excel_file_path

#         # Read file into BytesIO
#         with open(temp_path, 'rb') as f:
#             bytes_io = BytesIO(f.read())

#         # Replace with your actual function import
#         # result = read_excel(bytes_io)

#         # For demonstration
#         result = pl.read_excel(source=bytes_io)

#         # Assertions
#         assert isinstance(result, pl.DataFrame)
#         assert result.shape == expected_data.shape
#         assert result.columns == expected_data.columns
#         assert result.equals(expected_data)

#     def test_read_excel_empty_file(self):
#         """Test read_excel with empty Excel file"""
#         # Create empty DataFrame
#         empty_data = pl.DataFrame()

#         temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
#         temp_path = Path(temp_file.name)
#         temp_file.close()

#         try:
#             empty_data.write_excel(temp_path)

#             # Test with UploadFile
#             upload_file = MockUploadFile(str(temp_path))
#             result = pl.read_excel(source=upload_file.file.path)

#             assert isinstance(result, pl.DataFrame)
#             assert result.shape[0] == 0  # No rows
#         finally:
#             temp_path.unlink(missing_ok=True)

#     def test_type_checking(self):
#         """Test that the function correctly identifies input type"""
#         temp_path, _ = create_test_excel_file()

#         try:
#             upload_file = MockUploadFile(str(temp_path))

#             # Check type detection
#             assert isinstance(upload_file, MockUploadFile)
#             assert hasattr(upload_file, 'file')
#             assert hasattr(upload_file.file, 'path')

#             # Check bytes type
#             with open(temp_path, 'rb') as f:
#                 file_bytes = f.read()
#             assert isinstance(file_bytes, bytes)
#         finally:
#             temp_path.unlink(missing_ok=True)

#     def test_read_excel_invalid_file(self):
#         """Test read_excel with invalid/corrupted file"""
#         # Create a text file pretending to be Excel
#         temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
#         temp_path = Path(temp_file.name)
#         temp_file.write(b"This is not a valid Excel file")
#         temp_file.close()

#         try:
#             with pytest.raises(Exception):  # Polars will raise an exception
#                 pl.read_excel(source=str(temp_path))
#         finally:
#             temp_path.unlink(missing_ok=True)


# # Integration test with actual function
# class TestReadExcelIntegration:
#     """Integration tests using the actual read_excel function"""


#     @pytest.mark.parametrize("input_type", ["upload_file", "bytes"])
#     def test_both_input_types(self, input_type):
#         """Parametrized test for both input types"""
#         temp_path, expected_data = create_test_excel_file()

#         try:
#             if input_type == "upload_file":
#                 upload_file = MockUploadFile(str(temp_path))
#                 # result = read_excel(upload_file)
#                 result = pl.read_excel(source=upload_file.file.path)
#             else:
#                 with open(temp_path, 'rb') as f:
#                     file_bytes = f.read()
#                 # result = read_excel(file_bytes)
#                 result = pl.read_excel(source=file_bytes)

#             assert result.equals(expected_data)
#         finally:
#             temp_path.unlink(missing_ok=True)
