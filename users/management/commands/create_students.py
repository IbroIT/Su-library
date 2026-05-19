from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


User = get_user_model()


class Command(BaseCommand):
    help = "Create or update student accounts with predictable email logins."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=200,
            help="How many student accounts to create.",
        )
        parser.add_argument(
            "--password",
            default="123456",
            help="Password that will be set for every student.",
        )
        parser.add_argument(
            "--prefix",
            default="student",
            help="Username/email prefix. Example: student001.",
        )
        parser.add_argument(
            "--email-domain",
            default="students.su-library.kg",
            help="Email domain used for student logins.",
        )
        parser.add_argument(
            "--start-index",
            type=int,
            default=1,
            help="Starting number for generated students.",
        )
        parser.add_argument(
            "--group",
            default=None,
            help="Optional group value for every created student.",
        )
        parser.add_argument(
            "--course",
            type=int,
            default=None,
            help="Optional course value for every created student.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        password = options["password"]
        prefix = options["prefix"].strip()
        email_domain = options["email_domain"].strip().lower()
        start_index = options["start_index"]
        group = options["group"]
        course = options["course"]

        if count < 1:
            raise CommandError("--count must be greater than 0.")
        if start_index < 1:
            raise CommandError("--start-index must be greater than 0.")
        if not prefix:
            raise CommandError("--prefix cannot be empty.")
        if not email_domain or "@" in email_domain:
            raise CommandError("--email-domain must be a domain only, for example students.su-library.kg.")

        students = []
        for index in range(start_index, start_index + count):
            username = f"{prefix}{index:03d}"
            email = f"{username}@{email_domain}"
            students.append(
                {
                    "index": index,
                    "username": username,
                    "email": email,
                }
            )

        conflicts = self._find_conflicts(students)
        if conflicts:
            raise CommandError(
                "Cannot create students because of account conflicts:\n- "
                + "\n- ".join(conflicts)
            )

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for student in students:
                user, created = User.objects.get_or_create(
                    email=student["email"],
                    defaults={
                        "username": student["username"],
                        "is_active": True,
                    },
                )

                user.username = student["username"]
                user.is_active = True

                if group is not None:
                    user.group = group
                if course is not None:
                    user.course = course

                user.set_password(password)
                user.save()

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Students ready: {count} total, {created_count} created, {updated_count} updated."
        ))
        self.stdout.write("Credentials:")
        for student in students:
            self.stdout.write(f'{student["email"]} | {password}')

    def _find_conflicts(self, students):
        conflicts = []

        for student in students:
            email = student["email"]
            username = student["username"]

            email_owner = User.objects.filter(email=email).first()
            if email_owner and (email_owner.is_staff or email_owner.is_superuser):
                conflicts.append(
                    f'email "{email}" belongs to an admin/staff account'
                )

            username_owner = User.objects.filter(username=username).exclude(email=email).first()
            if username_owner:
                conflicts.append(
                    f'username "{username}" already belongs to "{username_owner.email}"'
                )

        return conflicts
