from django.contrib import admin
from .models import Scanner, ScanRun, ScanFinding

@admin.register(Scanner)
class ScannerAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "created")

@admin.register(ScanRun)
class ScanRunAdmin(admin.ModelAdmin):
    list_display = ("scanner", "status", "started", "finished")

@admin.register(ScanFinding)
class ScanFindingAdmin(admin.ModelAdmin):
    list_display = ("run", "summary")
