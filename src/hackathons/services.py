import csv
from io import StringIO

from ninja import UploadedFile


def get_emails_from_csv(file: UploadedFile) -> list[str]:
    file_data = file.read().decode(
        "utf-8-sig"
    )  # Используем 'utf-8-sig' для удаления BOM
    csv_reader = csv.reader(StringIO(file_data), delimiter=",")
    emails = [row[0].strip() for row in csv_reader if row]

    return emails
