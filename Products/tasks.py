import csv
from decimal import Decimal, InvalidOperation

import requests

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

import cloudinary.uploader

from .models import Products, BulkImport
from .services.utils import create_product_key


User = get_user_model()


def send_import_progress(
    import_id,
    status,
    processed,
    total,
    created,
    skipped,
    failed
):

    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(
        f"bulk_import_{import_id}",

        {
            "type": "bulk_import_progress",

            "import_id": str(import_id),

            "status": status,

            "processed": processed,

            "total": total,

            "created": created,

            "skipped": skipped,

            "failed": failed,

            "percentage": (
                round(
                    processed / total * 100,
                    2
                )
                if total
                else 0
            )
        }
    )


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_kwargs={
        "max_retries": 3
    }
)
def bulk_create_products(
    self,
    import_id
):

    bulk_import = BulkImport.objects.select_related(
        "uploaded_by",
        "category"
    ).get(
        id=import_id
    )

    bulk_import.status = (
        BulkImport.Status.PROCESSING
    )

    bulk_import.started_at = timezone.now()

    bulk_import.save(
        update_fields=[
            "status",
            "started_at"
        ]
    )

    created_count = 0
    skipped_count = 0
    failed_count = 0
    processed = 0

    try:

        # --------------------------------
        # Download CSV from Cloudinary
        # --------------------------------

        response = requests.get(
            bulk_import.csv_url,
            timeout=60
        )

        response.raise_for_status()

        csv_content = response.content.decode(
            "utf-8-sig"
        )

        rows = list(
            csv.DictReader(
                csv_content.splitlines()
            )
        )

        total = len(rows)

        bulk_import.total_rows = total

        bulk_import.save(
            update_fields=[
                "total_rows"
            ]
        )

        # --------------------------------
        # Send initial progress
        # --------------------------------

        send_import_progress(
            import_id=bulk_import.id,
            status="processing",
            processed=0,
            total=total,
            created=0,
            skipped=0,
            failed=0
        )

        # --------------------------------
        # Process rows
        # --------------------------------

        for row_number, row in enumerate(
            rows,
            start=2
        ):

            processed += 1

            try:

                # -------------------------
                # Read CSV data
                # -------------------------

                brand = row.get(
                    "brand",
                    ""
                ).strip()

                name = row.get(
                    "title",
                    ""
                ).strip()

                image_url = row.get(
                    "extraLargeUrl",
                    ""
                ).strip()

                package_quantity = Decimal(
                    row.get(
                        "package_quantity",
                        "0"
                    ).strip()
                )

                package_unit = row.get(
                    "package_unit",
                    ""
                ).strip()

                price_inr = Decimal(
                    row.get(
                        "price_inr",
                        "0"
                    ).strip()
                )

                # -------------------------
                # Basic validation
                # -------------------------

                if not name:

                    raise ValueError(
                        "Product title is empty"
                    )

                if not brand:

                    raise ValueError(
                        "Brand is empty"
                    )

                if not image_url:

                    raise ValueError(
                        "Image URL is empty"
                    )

                if package_quantity <= 0:

                    raise ValueError(
                        "Package quantity must be > 0"
                    )

                if price_inr < 0:

                    raise ValueError(
                        "Price cannot be negative"
                    )

                # -------------------------
                # Product key
                # -------------------------

                product_key = (
                    create_product_key(
                        brand=brand,
                        name=name,
                        package_quantity=package_quantity,
                        package_unit=package_unit
                    )
                )

                # -------------------------
                # Duplicate check
                # -------------------------

                if Products.objects.filter(
                    product_key=product_key
                ).exists():

                    skipped_count += 1

                    continue

                # Source URL duplicate
                if Products.objects.filter(
                    source_url=image_url
                ).exists():

                    skipped_count += 1

                    continue

                # -------------------------
                # Download image
                # -------------------------

                image_response = requests.get(
                    image_url,
                    timeout=30
                )

                image_response.raise_for_status()

                # -------------------------
                # Cloudinary upload
                # -------------------------

                cloudinary_result = (
                    cloudinary.uploader.upload(
                        image_response.content,
                        folder="swiftcart/products"
                    )
                )

                public_id = (
                    cloudinary_result[
                        "public_id"
                    ]
                )

                # -------------------------
                # Create product
                # -------------------------

                try:

                    with transaction.atomic():

                        Products.objects.create(

                            user=bulk_import.uploaded_by,

                            category=bulk_import.category,

                            name=name,

                            brand=brand,

                            source_url=image_url,

                            product_key=product_key,

                            image=public_id,

                            package_quantity=
                                package_quantity,

                            package_unit=
                                package_unit,

                            price_inr=
                                price_inr
                        )

                except IntegrityError:

                    # Race condition protection
                    skipped_count += 1

                    continue

                created_count += 1

            except (
                InvalidOperation,
                ValueError,
                requests.RequestException
            ) as error:

                failed_count += 1

                print(
                    f"Row {row_number} failed: "
                    f"{error}"
                )

            except Exception as error:

                failed_count += 1

                print(
                    f"Unexpected error "
                    f"row {row_number}: "
                    f"{error}"
                )

            # -------------------------
            # Update DB progress
            # -------------------------

            if (
                processed % 10 == 0
                or processed == total
            ):

                bulk_import.created_count = (
                    created_count
                )

                bulk_import.skipped_count = (
                    skipped_count
                )

                bulk_import.failed_count = (
                    failed_count
                )

                bulk_import.save(
                    update_fields=[
                        "created_count",
                        "skipped_count",
                        "failed_count"
                    ]
                )

                send_import_progress(
                    import_id=bulk_import.id,
                    status="processing",
                    processed=processed,
                    total=total,
                    created=created_count,
                    skipped=skipped_count,
                    failed=failed_count
                )

        # --------------------------------
        # Completed
        # --------------------------------

        bulk_import.status = (
            BulkImport.Status.COMPLETED
        )

        bulk_import.created_count = (
            created_count
        )

        bulk_import.skipped_count = (
            skipped_count
        )

        bulk_import.failed_count = (
            failed_count
        )

        bulk_import.completed_at = (
            timezone.now()
        )

        bulk_import.save()

        send_import_progress(
            import_id=bulk_import.id,
            status="completed",
            processed=processed,
            total=total,
            created=created_count,
            skipped=skipped_count,
            failed=failed_count
        )

        return {
            "status": "completed",
            "total": total,
            "created": created_count,
            "skipped": skipped_count,
            "failed": failed_count
        }

    except Exception as error:

        bulk_import.status = (
            BulkImport.Status.FAILED
        )

        bulk_import.error_message = str(
            error
        )

        bulk_import.completed_at = (
            timezone.now()
        )

        bulk_import.save()

        send_import_progress(
            import_id=bulk_import.id,
            status="failed",
            processed=processed,
            total=bulk_import.total_rows,
            created=created_count,
            skipped=skipped_count,
            failed=failed_count
        )

        raise