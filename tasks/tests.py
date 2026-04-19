import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from allauth.socialaccount.models import SocialAccount, SocialLogin

from config import settings as project_settings

from .adapters import HangarinSocialAccountAdapter
from .bootstrap import _run_initial_setup
from .models import Category, Note, Priority, StatusChoices, SubTask, Task


class DatabaseSettingsTests(SimpleTestCase):
    def test_build_database_settings_accepts_vercel_postgres_url_variants(self):
        database_settings = project_settings.build_database_settings(
            "prisma+postgres://demo-user:demo-pass@example.com:5432/hangarin?sslmode=require"
        )

        self.assertEqual(
            database_settings["default"]["ENGINE"],
            "django.db.backends.postgresql",
        )
        self.assertEqual(database_settings["default"]["NAME"], "hangarin")
        self.assertEqual(database_settings["default"]["HOST"], "example.com")
        self.assertEqual(database_settings["default"]["PORT"], "5432")
        self.assertEqual(database_settings["default"]["OPTIONS"]["sslmode"], "require")

    def test_build_database_settings_falls_back_to_sqlite_on_vercel_for_invalid_url(self):
        with patch.object(project_settings, "IS_VERCEL", True):
            database_settings = project_settings.build_database_settings(
                "mysql://demo-user:demo-pass@example.com:3306/hangarin"
            )

        self.assertEqual(
            database_settings["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )
        self.assertTrue(str(database_settings["default"]["NAME"]).endswith("db.sqlite3"))

    def test_build_database_settings_raises_for_invalid_local_database_url(self):
        with patch.object(project_settings, "IS_VERCEL", False):
            with self.assertRaises(ValueError):
                project_settings.build_database_settings(
                    "mysql://demo-user:demo-pass@example.com:3306/hangarin"
                )


class FrontendViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="viewer",
            password="safe-password-123",
        )
        cls.category = Category.objects.create(name="Operations")
        cls.priority = Priority.objects.create(name="High")
        cls.task = Task.objects.create(
            title="Finish runway audit",
            description="Finalize the operational runway checklist.",
            status=StatusChoices.IN_PROGRESS,
            deadline=timezone.now() + timedelta(days=2),
            category=cls.category,
            priority=cls.priority,
        )
        SubTask.objects.create(
            task=cls.task,
            title="Collect field signatures",
            status=StatusChoices.PENDING,
        )
        Note.objects.create(
            task=cls.task,
            content="Pending approval from the hangar supervisor.",
        )

    def test_home_redirects_to_login_for_anonymous_users(self):
        response = self.client.get(reverse("tasks:home"))
        self.assertRedirects(response, reverse("tasks:login"))

    def test_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("tasks:login"),
            {"username": "viewer", "password": "safe-password-123"},
        )
        self.assertRedirects(response, reverse("tasks:dashboard"))

    @override_settings(GOOGLE_OAUTH_ENABLED=False, GITHUB_OAUTH_ENABLED=False)
    def test_login_page_hides_google_button_without_credentials(self):
        response = self.client.get(reverse("tasks:login"))
        self.assertNotContains(response, "Continue with Google")
        self.assertNotContains(response, "Continue with GitHub")

    @override_settings(PWA_ENABLED=False)
    def test_login_page_skips_pwa_registration_when_disabled(self):
        response = self.client.get(reverse("tasks:login"))
        self.assertNotContains(response, 'rel="manifest"')
        self.assertNotContains(response, "navigator.serviceWorker.register")

    @override_settings(GOOGLE_OAUTH_ENABLED=True, GITHUB_OAUTH_ENABLED=False)
    def test_login_page_shows_google_button_when_configured(self):
        response = self.client.get(reverse("tasks:login"))
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, "/accounts/google/login/?process=login")

    @override_settings(GOOGLE_OAUTH_ENABLED=False, GITHUB_OAUTH_ENABLED=True)
    def test_login_page_shows_github_button_when_configured(self):
        response = self.client.get(reverse("tasks:login"))
        self.assertContains(response, "Continue with GitHub")
        self.assertContains(response, "/accounts/github/login/?process=login")

    def test_dashboard_renders_backend_data(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:dashboard"))
        self.assertContains(response, "Finish runway audit")
        self.assertContains(response, "In Progress")

    def test_task_list_search_filters_results(self):
        Task.objects.create(
            title="Archive finance logs",
            description="Back office cleanup.",
            status=StatusChoices.COMPLETED,
            category=self.category,
            priority=self.priority,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:task-list"), {"q": "runway"})
        self.assertContains(response, "Finish runway audit")
        self.assertNotContains(response, "Archive finance logs")

    def test_logout_uses_post_and_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("tasks:logout"))
        self.assertRedirects(response, reverse("tasks:login"))

    def test_frontend_task_create_persists_record(self):
        self.client.force_login(self.user)
        deadline = (timezone.localtime(timezone.now()) + timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        response = self.client.post(
            reverse("tasks:task-create"),
            {
                "title": "Launch safety review",
                "description": "Prepare the final frontend-connected review.",
                "status": StatusChoices.PENDING,
                "category": self.category.pk,
                "priority": self.priority.pk,
                "deadline": deadline,
            },
        )
        self.assertRedirects(response, reverse("tasks:task-list"))
        self.assertTrue(Task.objects.filter(title="Launch safety review").exists())

    def test_dashboard_uses_social_account_name_when_user_fields_are_blank(self):
        social_user = get_user_model().objects.create_user(
            username="richo",
            email="richo@example.com",
            password="safe-password-123",
        )
        SocialAccount.objects.create(
            user=social_user,
            provider="github",
            uid="github-1",
            extra_data={
                "login": "richo",
                "name": "Richo Baterzal",
                "email": "richo@example.com",
            },
        )

        self.client.force_login(social_user)
        response = self.client.get(reverse("tasks:dashboard"))

        self.assertContains(response, "<strong>Richo Baterzal</strong>", html=True)
        self.assertContains(response, '<span class="user-pill__avatar">R</span>', html=True)

    def test_social_adapter_updates_existing_user_name_from_social_profile(self):
        social_user = get_user_model().objects.create_user(
            username="richo",
            email="richo@example.com",
            password="safe-password-123",
        )
        sociallogin = SocialLogin(
            user=social_user,
            account=SocialAccount(
                provider="google",
                uid="google-1",
                extra_data={
                    "name": "Richo Baterzal",
                    "given_name": "Richo",
                    "family_name": "Baterzal",
                    "email": "richo@example.com",
                },
            ),
        )

        adapter = HangarinSocialAccountAdapter()
        adapter.pre_social_login(RequestFactory().get("/accounts/google/login/"), sociallogin)
        social_user.refresh_from_db()

        self.assertEqual(social_user.first_name, "Richo")
        self.assertEqual(social_user.last_name, "Baterzal")


class BootstrapTests(TestCase):
    @override_settings(EPHEMERAL_SQLITE_DATABASE=True)
    @patch("tasks.bootstrap.call_command")
    def test_initial_setup_seeds_fake_data_for_ephemeral_demo_database(self, mock_call_command):
        with patch.dict(os.environ, {}, clear=True):
            _run_initial_setup()

        seeded_commands = [call.args[0] for call in mock_call_command.call_args_list]

        self.assertIn("seed_reference_data", seeded_commands)
        self.assertIn("seed_fake_data", seeded_commands)
