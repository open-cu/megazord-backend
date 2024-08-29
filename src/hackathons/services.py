import csv
from io import StringIO

from ninja import UploadedFile

from hackathons.models import UserRole
from resumes.models import Resume
from teams.models import Team


def get_emails_from_csv(file: UploadedFile) -> list[str]:
    file_data = file.read().decode("utf-8-sig")
    csv_reader = csv.reader(StringIO(file_data), delimiter=",")
    emails = [row[0].strip() for row in csv_reader if row]

    return emails


async def make_csv(hackathon) -> str:
    csv_output = StringIO()
    csv_writer = csv.writer(csv_output)

    csv_writer.writerow(["Team", "Email", "Full Name", "GitHub", "Role"])

    teams = Team.objects.filter(hackathon=hackathon).prefetch_related("team_members")

    async for team in teams:
        async for participant in team.team_members.all():
            try:
                resume = await Resume.objects.aget(
                    user=participant, hackathon=hackathon
                )
                github = resume.github or "N/A"
            except Resume.DoesNotExist:
                github = "N/A"

            try:
                user_role = await UserRole.objects.select_related("role").aget(
                    user=participant, hackathon=hackathon
                )
                role = user_role.role.name
            except UserRole.DoesNotExist:
                role = "N/A"

            csv_writer.writerow(
                [
                    team.name,
                    participant.email,
                    participant.username,
                    github,
                    role,
                ]
            )

    participants_without_team = hackathon.participants.exclude(
        id__in=teams.values_list("team_members__id", flat=True)
    )
    async for participant in participants_without_team:
        try:
            resume = await Resume.objects.aget(user=participant, hackathon=hackathon)
            github = resume.github or "N/A"
        except Resume.DoesNotExist:
            github = "N/A"

        try:
            user_role = await UserRole.objects.select_related("role").aget(
                user=participant, hackathon=hackathon
            )
            role = user_role.role.name
        except UserRole.DoesNotExist:
            role = "N/A"

        csv_writer.writerow(
            [
                "No Team",
                participant.email,
                participant.username,
                github,
                role,
            ]
        )

    return csv_output.getvalue()
