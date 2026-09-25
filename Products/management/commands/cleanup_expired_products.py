from django.core.management.base import BaseCommand
from django.utils import timezone
from Products.models import Products  # Model path verify kar lein


class Command(BaseCommand):
    help = "Delete expired products from database based on expiry_date"

    def add_arguments(self, parser):
        # Optional --dry-run flag for safe testing
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many expired products would be deleted without actually deleting them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        expired_products = Products.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=now
        )

        count = expired_products.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No expired products found."))
            return

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(f"[DRY-RUN] Found {count} expired product(s) that would be deleted.")
            )
        else:
            # Single query delete
            deleted_total, deleted_details = expired_products.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully deleted {deleted_total} expired product(s).")
            )