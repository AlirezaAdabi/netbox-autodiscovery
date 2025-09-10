from django.utils import timezone
from dcim.models import Device, Interface, DeviceRole, DeviceType, Site, Manufacturer
from ipam.models import VLAN
from .snmp_helpers import snmp_walk, snmp_get
from ..models import ScanFinding


def run_cisco_scan(params: dict, run, fake: bool = False):
    """
    Discover a Cisco switch via SNMP.
    Params example:
        {"hostname": "192.168.1.10", "community": "public"}
    """

    hostname = params.get("hostname")
    community = params.get("community", "public")
    if not hostname:
        raise ValueError("No hostname provided for Cisco scan")

    def log_step(msg: str):
        """Helper to append to log progressively"""
        run.log = (run.log or "") + f"\n{msg}"
        run.save(update_fields=["log"])

    log_step(f"Connecting to {hostname} via SNMP community='{community}'")

    # ----------------------------------------------------------------------
    # Fake mode
    # ----------------------------------------------------------------------
    if fake:
        manufacturer, _ = Manufacturer.objects.get_or_create(name="Cisco", defaults={"slug": "cisco"})
        dtype, _ = DeviceType.objects.get_or_create(
            model="Cisco 2960",
            manufacturer=manufacturer,
            defaults={"slug": "cisco-2960"}
        )
        site, _ = Site.objects.get_or_create(name="Default", defaults={"slug": "default"})

        device, _ = Device.objects.get_or_create(
            name=hostname,
            defaults={"device_type": dtype, "status": "active", "site": site},
        )

        iface1, _ = Interface.objects.get_or_create(device=device, name="Gig0/1")
        iface2, _ = Interface.objects.get_or_create(device=device, name="Gig0/2")

        vlan10, _ = VLAN.objects.get_or_create(vid=10, defaults={"name": "Users"})
        vlan20, _ = VLAN.objects.get_or_create(vid=20, defaults={"name": "Servers"})

        iface1.mode = "access"
        iface1.untagged_vlan = vlan10
        iface1.save()

        iface2.mode = "tagged"
        iface2.tagged_vlans.set([vlan10, vlan20])
        iface2.save()

        # ✅ Record findings
        from ..models import ScanFinding
        ScanFinding.objects.create(
            run=run,
            summary="Fake Cisco device discovered",
            details={"device": device.name}
        )
        ScanFinding.objects.create(
            run=run,
            summary="Interfaces discovered",
            details={"interfaces": [iface1.name, iface2.name]}
        )
        ScanFinding.objects.create(
            run=run,
            summary="VLANs discovered",
            details={"vlans": [vlan10.vid, vlan20.vid]}
        )

        log_step("✅ Fake Cisco scan complete. Created device, interfaces, VLANs, and assignments.")
        run.stats = {"interfaces": 2, "vlans": 2, "assignments": 2}
        run.finished = timezone.now()
        run.save()
        return run.stats

    # ----------------------------------------------------------------------
    # Real SNMP discovery
    # ----------------------------------------------------------------------
    stats = {"interfaces": 0, "vlans": 0, "assignments": 0}

    # Step 1: System info
    try:
        sysname = snmp_get(hostname, community, "1.3.6.1.2.1.1.5.0")
        sysdescr = snmp_get(hostname, community, "1.3.6.1.2.1.1.1.0")
        serial = snmp_get(hostname, community, "1.3.6.1.4.1.9.3.6.3")

        log_step(f"System name: {sysname or hostname}")
        if sysdescr:
            log_step(f"System description: {sysdescr}")
        if serial:
            log_step(f"Serial: {serial}")

        manufacturer, _ = Manufacturer.objects.get_or_create(name="Cisco", defaults={"slug": "cisco"})
        role, _ = DeviceRole.objects.get_or_create(name="Switch", defaults={"slug": "switch"})
        dtype, _ = DeviceType.objects.get_or_create(
            model="Generic Cisco Switch",
            manufacturer=manufacturer,
            defaults={"slug": "generic-cisco"}
        )
        site, _ = Site.objects.get_or_create(name="Default", defaults={"slug": "default"})

        device, created = Device.objects.get_or_create(
            name=sysname or hostname,
            defaults={"role": role, "device_type": dtype, "status": "active", "site": site},
        )
        if created:
            ScanFinding.objects.create(
                run=run,
                summary="New Cisco device discovered",
                details={"hostname": device.name, "serial": device.serial}
            )
        else:
            ScanFinding.objects.create(
                run=run,
                summary="Cisco device updated",
                details={"hostname": device.name, "serial": device.serial}
            )
        if sysdescr:
            device.comments = (device.comments or "") + f"\nDiscovered: {sysdescr}"
        if serial:
            device.serial = serial
        device.save()
    except Exception as e:
        log_step(f"❌ Failed system info discovery: {e}")
        return stats  # cannot continue without a device

    # Step 2: Interfaces
    try:
        log_step("Walking SNMP for interfaces...")
        if_names = snmp_walk(hostname, community, "1.3.6.1.2.1.31.1.1.1.1")
        if_types = snmp_walk(hostname, community, "1.3.6.1.2.1.2.2.1.3")
        if_admin = snmp_walk(hostname, community, "1.3.6.1.2.1.2.2.1.7")
        if_oper = snmp_walk(hostname, community, "1.3.6.1.2.1.2.2.1.8")

        for idx, if_name in if_names.items():
            iface, _ = Interface.objects.get_or_create(device=device, name=if_name)
            iface.type = "1000base-t" if if_types.get(idx) == "6" else "other"
            iface.enabled = if_admin.get(idx) == "1"
            iface.save()
        stats["interfaces"] = len(if_names)
        log_step(f"✅ Discovered {len(if_names)} interfaces.")
    except Exception as e:
        log_step(f"❌ Failed interface discovery: {e}")

    # Step 3: VLANs
    vlan_map = {}
    try:
        log_step("Walking SNMP for VLANs...")
        vlan_ids = snmp_walk(hostname, community, "1.3.6.1.4.1.9.9.46.1.3.1.1.1")
        vlan_names = snmp_walk(hostname, community, "1.3.6.1.4.1.9.9.46.1.3.1.1.4")

        for idx, vid in vlan_ids.items():
            try:
                vid_int = int(vid)
            except Exception:
                continue
            name = vlan_names.get(idx, f"VLAN{vid_int}")
            vlan, _ = VLAN.objects.get_or_create(vid=vid_int, defaults={"name": name})
            ScanFinding.objects.create(
                run=run,
                summary="VLAN discovered",
                details={"vid": vlan.vid, "name": vlan.name}
            )

            if vlan.name != name:
                vlan.name = name
                vlan.save()
            vlan_map[idx] = vlan
        stats["vlans"] = len(vlan_map)
        log_step(f"✅ Discovered {len(vlan_map)} VLANs.")
    except Exception as e:
        log_step(f"❌ Failed VLAN discovery: {e}")

    # Step 4: VLAN assignments
    try:
        log_step("Walking SNMP for VLAN ↔ interface assignments...")
        access_vlans = snmp_walk(hostname, community, "1.3.6.1.4.1.9.9.68.1.2.2.1.2")
        trunk_vlans = snmp_walk(hostname, community, "1.3.6.1.4.1.9.9.46.1.6.1.1.4")

        assignments = 0
        for idx, vlan_id in access_vlans.items():
            if_name = if_names.get(idx)
            if not if_name:
                continue
            try:
                vlan = VLAN.objects.get(vid=int(vlan_id))
            except VLAN.DoesNotExist:
                continue
            iface = Interface.objects.filter(device=device, name=if_name).first()
            if iface:
                iface.mode = "access"
                iface.untagged_vlan = vlan
                iface.save()
                assignments += 1

        for idx, vlan_mask in trunk_vlans.items():
            if_name = if_names.get(idx)
            if not if_name:
                continue
            iface = Interface.objects.filter(device=device, name=if_name).first()
            if not iface:
                continue

            iface.mode = "tagged"
            enabled_vlans = []
            try:
                mask = int(vlan_mask)
                for vid in range(1, 4095):
                    if mask & (1 << (vid % 32)):
                        try:
                            vlan = VLAN.objects.get(vid=vid)
                            enabled_vlans.append(vlan)
                        except VLAN.DoesNotExist:
                            continue
            except Exception:
                pass

            if enabled_vlans:
                iface.tagged_vlans.set(enabled_vlans)
                iface.save()
                assignments += 1

        stats["assignments"] = assignments
        log_step(f"✅ Assigned VLANs on {assignments} interfaces.")
    except Exception as e:
        log_step(f"❌ Failed VLAN assignment discovery: {e}")

    # Finalize
    run.stats = stats
    run.finished = timezone.now()
    run.save()

    return run.stats
