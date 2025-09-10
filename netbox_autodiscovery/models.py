from django.db import models
from django.utils.translation import gettext_lazy as _
from netbox.models import RestrictedQuerySet 
from django.urls import reverse

class Scanner(models.Model):
    class ScannerType(models.TextChoices):
        RANGE = "range", _("Range Scan")
        CISCO = "cisco", _("Cisco Switch Scan")

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=ScannerType.choices)
    params = models.JSONField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    # NetBox permissions-aware queryset
    objects = RestrictedQuerySet.as_manager()


    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def get_absolute_url(self):
        return reverse("plugins:netbox_autodiscovery:scanner", args=[self.pk])
    

class ScanRun(models.Model):
    class RunStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        SUCCESS = "success", _("Success")
        FAILED = "failed", _("Failed")

    scanner = models.ForeignKey(Scanner, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=20, choices=RunStatus.choices, default=RunStatus.PENDING)
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)
    log = models.TextField(blank=True)
    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return f"Run {self.id} of {self.scanner} [{self.status}]"
    
    def get_absolute_url(self):
        return reverse("plugins:netbox_autodiscovery:scanrun", args=[self.pk])


class ScanFinding(models.Model):
    run = models.ForeignKey(ScanRun, on_delete=models.CASCADE, related_name="findings")
    summary = models.CharField(max_length=255)
    details = models.JSONField(blank=True, null=True)

    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return f"Finding for run {self.run_id}: {self.summary}"

