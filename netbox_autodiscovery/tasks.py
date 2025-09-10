# netbox_autodiscovery/tasks.py
from django.utils import timezone
from .models import ScanRun, Scanner
from .discovery.range_scan import run_network_scan
from .discovery.cisco_scan import run_cisco_scan

def run_scanner(run_id):
    run = ScanRun.objects.get(pk=run_id)
    run.status = ScanRun.RunStatus.RUNNING
    run.started = timezone.now()
    run.save()

    try:
        scanner = run.scanner
        if scanner.type == Scanner.ScannerType.RANGE:
            fake = scanner.params.get("fake_mode", False)
            stats = run_network_scan(scanner.params or {}, run, fake=fake)
            run.stats = stats
            run.status = ScanRun.RunStatus.SUCCESS
        elif scanner.type == Scanner.ScannerType.CISCO:
            fake = scanner.params.get("fake_mode", False)
            stats = run_cisco_scan(scanner.params or {}, run, fake=fake)
            run.stats = stats
            run.status = ScanRun.RunStatus.SUCCESS
        else:
            run.log = f"Unsupported scanner type: {scanner.type}"
            run.status = ScanRun.RunStatus.FAILED
    except Exception as e:
        run.status = ScanRun.RunStatus.FAILED
        run.log = (run.log or "") + f"\nError: {e!r}"
    finally:
        run.finished = timezone.now()
        run.save()
