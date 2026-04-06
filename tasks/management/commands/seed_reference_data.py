from django.core.management.base import BaseCommand

from tasks.models import Category, Priority


class Command(BaseCommand):
    help = "Seed fixed Priority and Category records."

    def handle(self, *args, **options):
        priorities = ["high", "medium", "low", "critical", "optional"]
        categories = ["Work", "School", "Personal", "Finance", "Projects"]

        for name in priorities:
            Priority.objects.get_or_create(name=name)
        for name in categories:
            Category.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Reference data seeded successfully."))
