from django.core.management.base import BaseCommand
from background_task.models import Task
import time

class Command(BaseCommand):
    help = 'Start the background task processor'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                'Starting background task processor...\n'
                'This command will run indefinitely. Press Ctrl+C to stop.\n'
                'Make sure you have configured your R2 credentials in the environment variables.'
            )
        )
        
        # Import here to ensure Django is fully loaded
        from background_task.tasks import tasks
        tasks.run_worker()