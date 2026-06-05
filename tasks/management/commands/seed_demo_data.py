from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Category, Note, Priority, StatusChoices, SubTask, Task


PRIORITIES = ["Critical", "High", "Medium", "Low"]
CATEGORIES = ["School", "Personal", "Projects", "Finance", "Work"]

DEMO_TASKS = [
    {
        "title": "Prepare final project presentation",
        "description": "Build the slides, rehearse the flow, and prepare backup notes.",
        "status": StatusChoices.IN_PROGRESS,
        "deadline_days": 2,
        "priority": "High",
        "category": "School",
        "subtasks": [
            ("Create slide outline", StatusChoices.COMPLETED),
            ("Add screenshots and examples", StatusChoices.IN_PROGRESS),
            ("Practice the five-minute pitch", StatusChoices.PENDING),
        ],
        "notes": [
            "Keep the demo short and focus on the working dashboard.",
            "Mention deployment status and remaining improvements.",
        ],
    },
    {
        "title": "Review PythonAnywhere deployment",
        "description": "Check static files, OAuth configuration, and production settings.",
        "status": StatusChoices.IN_PROGRESS,
        "deadline_days": 1,
        "priority": "Critical",
        "category": "Projects",
        "subtasks": [
            ("Confirm WSGI environment variables", StatusChoices.PENDING),
            ("Reload the web app after pulling changes", StatusChoices.PENDING),
            ("Test Google and GitHub callbacks", StatusChoices.PENDING),
        ],
        "notes": [
            "Google and GitHub callbacks must use the live HTTPS domain.",
        ],
    },
    {
        "title": "Organize weekly task list",
        "description": "Plan priorities for school, personal work, and project deadlines.",
        "status": StatusChoices.PENDING,
        "deadline_days": 5,
        "priority": "Medium",
        "category": "Personal",
        "subtasks": [
            ("Sort urgent work first", StatusChoices.PENDING),
            ("Archive completed notes", StatusChoices.PENDING),
        ],
        "notes": [
            "Use categories to keep the dashboard easier to scan.",
        ],
    },
    {
        "title": "Track allowance and expenses",
        "description": "Record recent spending and check what remains for the week.",
        "status": StatusChoices.PENDING,
        "deadline_days": 7,
        "priority": "Low",
        "category": "Finance",
        "subtasks": [
            ("List transportation costs", StatusChoices.PENDING),
            ("Update food budget", StatusChoices.PENDING),
        ],
        "notes": [
            "Keep receipts grouped by date.",
        ],
    },
    {
        "title": "Submit task manager documentation",
        "description": "Write setup steps, deployment notes, and login instructions.",
        "status": StatusChoices.COMPLETED,
        "deadline_days": -1,
        "priority": "High",
        "category": "Work",
        "subtasks": [
            ("Document local run commands", StatusChoices.COMPLETED),
            ("Add PythonAnywhere deployment steps", StatusChoices.COMPLETED),
        ],
        "notes": [
            "README includes seed commands and social login setup.",
        ],
    },
]


class Command(BaseCommand):
    help = "Seed deterministic demo data for the Hangarin task dashboard."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-demo",
            action="store_true",
            help="Remove existing demo tasks before creating them again.",
        )

    def handle(self, *args, **options):
        if options["clear_demo"]:
            Task.objects.filter(title__in=[task["title"] for task in DEMO_TASKS]).delete()

        priorities = {
            name: Priority.objects.get_or_create(name=name)[0]
            for name in PRIORITIES
        }
        categories = {
            name: Category.objects.get_or_create(name=name)[0]
            for name in CATEGORIES
        }

        now = timezone.now()
        created_count = 0
        updated_count = 0

        for demo_task in DEMO_TASKS:
            task, created = Task.objects.update_or_create(
                title=demo_task["title"],
                defaults={
                    "description": demo_task["description"],
                    "status": demo_task["status"],
                    "deadline": now + timedelta(days=demo_task["deadline_days"]),
                    "priority": priorities[demo_task["priority"]],
                    "category": categories[demo_task["category"]],
                },
            )

            task.subtasks.all().delete()
            task.notes.all().delete()

            for title, status in demo_task["subtasks"]:
                SubTask.objects.create(task=task, title=title, status=status)

            for content in demo_task["notes"]:
                Note.objects.create(task=task, content=content)

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data seeded: {created_count} created, {updated_count} updated."
            )
        )
