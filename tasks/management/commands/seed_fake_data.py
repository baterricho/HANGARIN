import random

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from tasks.models import Category, Note, Priority, StatusChoices, SubTask, Task


class Command(BaseCommand):
    help = "Generate fake Task, SubTask, and Note records using Faker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tasks",
            type=int,
            default=20,
            help="Number of tasks to generate.",
        )
        parser.add_argument(
            "--max-subtasks",
            type=int,
            default=4,
            help="Maximum subtasks generated per task.",
        )
        parser.add_argument(
            "--max-notes",
            type=int,
            default=3,
            help="Maximum notes generated per task.",
        )

    def handle(self, *args, **options):
        priorities = list(Priority.objects.all())
        categories = list(Category.objects.all())

        if not priorities or not categories:
            self.stdout.write(
                self.style.ERROR(
                    "Priority and Category records are required. "
                    "Run `python manage.py seed_reference_data` first."
                )
            )
            return

        fake = Faker()
        statuses = [choice for choice, _ in StatusChoices.choices]
        task_count = options["tasks"]
        max_subtasks = max(1, options["max_subtasks"])
        max_notes = max(1, options["max_notes"])

        for _ in range(task_count):
            task = Task.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=3),
                status=fake.random_element(elements=statuses),
                deadline=timezone.make_aware(fake.date_time_this_month()),
                priority=fake.random_element(elements=priorities),
                category=fake.random_element(elements=categories),
            )

            for _ in range(random.randint(1, max_subtasks)):
                SubTask.objects.create(
                    task=task,
                    title=fake.sentence(nb_words=5),
                    status=fake.random_element(elements=statuses),
                )

            for _ in range(random.randint(1, max_notes)):
                Note.objects.create(
                    task=task,
                    content=fake.paragraph(nb_sentences=2),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {task_count} tasks with fake subtasks and notes."
            )
        )
