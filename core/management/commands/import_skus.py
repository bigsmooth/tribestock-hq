from __future__ import annotations
import csv, json, sys
from pathlib import Path
from typing import Iterable, Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import SKU, Hub, Inventory


REQUIRED_FIELDS = ("sku_code", "name")
OPTIONAL_FIELDS = ("color", "size", "barcode", "active")


def _normalize_bool(val: Any) -> bool | None:
    if val is None or val == "":
        return None
    s = str(val).strip().lower()
    if s in ("1", "true", "t", "yes", "y", "on"):
        return True
    if s in ("0", "false", "f", "no", "n", "off"):
        return False
    return None


def _load_csv(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # header is line 1
            if not row.get("sku_code") or not row.get("name"):
                raise CommandError(f"Missing sku_code/name at CSV line {i}")
            yield row


def _load_json(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise CommandError("JSON must be an array of objects")
    for obj in data:
        if not obj.get("sku_code") or not obj.get("name"):
            raise CommandError("Every object needs sku_code and name")
        yield obj


class Command(BaseCommand):
    help = "Import or update SKUs from a CSV/JSON file. Creates zeroed Inventory rows for each new SKU across all hubs."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to CSV or JSON with SKUs.")
        parser.add_argument(
            "--format", choices=["csv", "json"], help="Override file format (auto by extension)."
        )
        parser.add_argument(
            "--no-upper", action="store_true",
            help="Do not force sku_code to UPPERCASE (default is to uppercase)."
        )
        parser.add_argument(
            "--deactivate-missing", action="store_true",
            help="Set active=False on SKUs not present in the input."
        )
        parser.add_argument(
            "--no-inventory", action="store_true",
            help="Do not ensure zeroed Inventory rows for new SKUs."
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Parse and show counts, but do not write to the database."
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts["path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        fmt = opts.get("format")
        if not fmt:
            ext = path.suffix.lower()
            fmt = "csv" if ext in (".csv",) else "json" if ext in (".json",) else None
        if fmt not in ("csv", "json"):
            raise CommandError("Unable to detect format. Use --format csv|json")

        loader = _load_csv if fmt == "csv" else _load_json
        rows = list(loader(path))

        # Build index of existing SKUs by normalized code
        existing = { (s.sku_code if opts["no_upper"] else s.sku_code.upper()): s for s in SKU.objects.all() }

        seen_codes = set()
        created = updated = unchanged = 0
        new_skus_for_inventory = []

        for row in rows:
            code = str(row.get("sku_code", "")).strip()
            name = str(row.get("name", "")).strip()
            if not opts["no_upper"]:
                code = code.upper()

            if not code or not name:
                raise CommandError("sku_code and name are required for every row")

            color  = (row.get("color") or "").strip()
            size   = (row.get("size") or "").strip()
            barcode = (row.get("barcode") or "").strip()
            active_in = _normalize_bool(row.get("active"))

            seen_codes.add(code)

            sku = existing.get(code)
            if not sku:
                if opts["dry_run"]:
                    created += 1
                    continue
                sku = SKU.objects.create(
                    sku_code=code,
                    name=name,
                    color=color,
                    size=size,
                    barcode=barcode,
                    active=True if active_in is None else bool(active_in),
                )
                existing[code] = sku
                created += 1
                if not opts["no_inventory"]:
                    new_skus_for_inventory.append(sku)
                continue

            # Update existing if fields differ
            changed = False
            if sku.name != name:
                sku.name = name; changed = True
            if color != "" and sku.color != color:
                sku.color = color; changed = True
            if size != "" and sku.size != size:
                sku.size = size; changed = True
            if barcode != "" and sku.barcode != barcode:
                sku.barcode = barcode; changed = True
            if active_in is not None and sku.active is not bool(active_in):
                sku.active = bool(active_in); changed = True

            if changed:
                if opts["dry_run"]:
                    updated += 1
                else:
                    sku.save()
                    updated += 1
            else:
                unchanged += 1

        # Deactivate missing SKUs
        deactivated = 0
        if opts["deactivate_missing"] and seen_codes:
            qs = SKU.objects.exclude(sku_code__in=seen_codes)
            if not opts["no_upper"]:
                qs = SKU.objects.exclude(sku_code__in=[c for c in seen_codes])
            if opts["dry_run"]:
                deactivated = qs.filter(active=True).count()
            else:
                deactivated = qs.filter(active=True).update(active=False)

        # Ensure inventory rows for newly created SKUs across all hubs
        ensured_inv = 0
        if new_skus_for_inventory and not opts["dry_run"] and not opts["no_inventory"]:
            hubs = list(Hub.objects.all())
            for sku in new_skus_for_inventory:
                for hub in hubs:
                    _, was = Inventory.objects.get_or_create(hub=hub, sku=sku, defaults={"quantity": 0})
                    ensured_inv += int(was)

        # Dry-run rollback
        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run: no changes were written."))  # transaction will rollback

        self.stdout.write(self.style.SUCCESS(
            f"SKUs → created: {created}, updated: {updated}, unchanged: {unchanged}, "
            f"deactivated: {deactivated}, inventory_rows_created: {ensured_inv}"
        ))

        if opts["dry_run"]:
            raise CommandError("Dry-run complete (no changes were saved).")
