import csv
from io import StringIO

from ninja import UploadedFile

from hackathons.models import UserRole
from resumes.models import Resume
from teams.models import Team


def get_emails_from_csv(file: UploadedFile) -> list[str]:
    file_data = file.read().decode(
        "utf-8-sig"
    )  # Используем 'utf-8-sig' для удаления BOM
    csv_reader = csv.reader(StringIO(file_data), delimiter=",")
    emails = [row[0].strip() for row in csv_reader if row]

    return emails


def make_csv(hackathon) -> str:
    # Создание объекта для записи CSV
    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)

    # Запись заголовков CSV-файла
    csv_writer.writerow(["Team", "Email", "Full Name", "GitHub", "Role"])

    # Получение списка команд и их участников
    teams = Team.objects.filter(hackathon=hackathon).prefetch_related("team_members")

    for team in teams:
        for participant in team.team_members.all():
            # Получаем резюме участника, если оно существует
            try:
                resume = Resume.objects.get(user=participant, hackathon=hackathon)
                github = (
                    resume.github or "N/A"
                )  # Используем GitHub из резюме, если оно существует
            except Resume.DoesNotExist:
                github = "N/A"  # Если резюме нет, то заполняем поле "N/A"

            # Получаем роль участника в хакатоне через таблицу UserRole
            try:
                user_role = UserRole.objects.get(user=participant, hackathon=hackathon)
                role = user_role.role.name
            except UserRole.DoesNotExist:
                role = "N/A"

            csv_writer.writerow(
                [
                    team.name,
                    participant.email,  # Почта участника
                    participant.username,  # Полное имя участника
                    github,  # GitHub пользователя из резюме
                    role,  # Роль участника в хакатоне
                ]
            )

    # Добавление участников без команды
    participants_without_team = hackathon.participants.exclude(
        id__in=teams.values_list("team_members__id", flat=True)
    )
    for participant in participants_without_team:
        # Получаем резюме участника, если оно существует
        try:
            resume = Resume.objects.get(user=participant, hackathon=hackathon)
            github = resume.github or "N/A"
        except Resume.DoesNotExist:
            github = "N/A"

        # Получаем роль участника в хакатоне через таблицу UserRole
        try:
            user_role = UserRole.objects.get(user=participant, hackathon=hackathon)
            role = user_role.role.name
        except UserRole.DoesNotExist:
            role = "N/A"

        csv_writer.writerow(
            [
                "No Team",
                participant.email,  # Почта участника
                participant.username,  # Полное имя участника
                github,  # GitHub пользователя из резюме
                role,  # Роль участника в хакатоне
            ]
        )

    # Возврат содержимого CSV как строки
    return csv_output.getvalue()
