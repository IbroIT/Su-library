from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


User = get_user_model()


class CreateStudentsCommandTests(TestCase):
    def test_creates_students_with_known_credentials(self):
        output = StringIO()

        call_command(
            "create_students",
            count=2,
            email_domain="students.test",
            stdout=output,
        )

        users = list(User.objects.order_by("email"))
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].email, "student001@students.test")
        self.assertEqual(users[1].email, "student002@students.test")
        self.assertTrue(users[0].check_password("123456"))
        self.assertTrue(users[1].check_password("123456"))
        self.assertTrue(users[0].is_active)
        self.assertTrue(users[1].is_active)

    def test_updates_existing_student_password_and_status(self):
        user = User.objects.create_user(
            username="student001",
            email="student001@students.test",
            password="oldpass",
            is_active=False,
        )

        call_command(
            "create_students",
            count=1,
            email_domain="students.test",
        )

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("123456"))

    def test_fails_when_username_is_used_by_another_account(self):
        User.objects.create_user(
            username="student001",
            email="other@students.test",
            password="secret123",
        )

        with self.assertRaises(CommandError):
            call_command(
                "create_students",
                count=1,
                email_domain="students.test",
            )
