import subprocess
import ipaddress
import socket
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipam.models import IPAddress
from ..models import ScanRun
from ..models import ScanFinding


# ---------------------------
# Helpers
# ---------------------------

def _ping_host(ip: str) -> bool:
    """Ping a single host once. Returns True if host responds."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except Exception:
        return False


def _reverse_dns(ip: str) -> str | None:
    """Try reverse DNS lookup."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


# ---------------------------
# Discovery core
# ---------------------------

def run_network_scan(params: dict, run: ScanRun, fake: bool = False, batch_size: int = 50):
    """
    Discover alive hosts in CIDR and save into NetBox IPAM.
    - params: {"cidr": "192.168.1.0/24"}
    - run: ScanRun instance (to update logs progressively)
    - fake: if True, simulate random results
    - batch_size: how many IPs per DB commit
    """

    cidr = params.get("cidr")
    if not cidr:
        raise ValueError("No cidr provided in scanner params")

    network = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(ip) for ip in network.hosts()]
    discovered = []
    created = 0
    existing = 0
    resolved = 0

    # Fake mode → choose some random IPs from range
# Fake mode → choose some random IPs from range
    if fake:
        alive_hosts = random.sample(hosts, min(5, len(hosts)))
        for ip in alive_hosts:
            discovered.append(ip)
            addr = f"{ip}/32"
            ip_obj, was_created = IPAddress.objects.get_or_create(address=addr)
            if was_created:
                ip_obj.description = "Discovered (FAKE) by AutoDiscovery"
                created += 1
                ScanFinding.objects.create(
                    run=run,
                    summary="New IP discovered (fake)",
                    details={"ip": ip}
                )
            else:
                existing += 1
                ScanFinding.objects.create(
                    run=run,
                    summary="Existing IP seen (fake)",
                    details={"ip": ip}
                )

            # fake hostname
            hostname = f"host-{ip.replace('.', '-')}.local"
            try:
                ip_obj.dns_name = hostname
            except Exception:
                ip_obj.description += f" Resolved hostname: {hostname}"
            resolved += 1
            ip_obj.save()

        run.log = "Fake scan complete."
        run.stats = {"cidr": cidr, "alive": len(discovered), "created": created, "resolved": resolved}
        run.save()
        return run.stats

    # Real scan with batching
    batch = []
    with ThreadPoolExecutor(max_workers=64) as ex:
        futures = {ex.submit(_ping_host, ip): ip for ip in hosts}
        total = len(futures)
        checked = 0

        for fut in as_completed(futures):
            checked += 1
            ip = futures[fut]
            try:
                if fut.result():
                    batch.append(ip)
            except Exception:
                pass

            # process batch
            if len(batch) >= batch_size or checked == total:
                # Reverse DNS in parallel
                with ThreadPoolExecutor(max_workers=16) as dns_ex:
                    dns_futures = {dns_ex.submit(_reverse_dns, ip): ip for ip in batch}
                    for df in as_completed(dns_futures):
                        ip = dns_futures[df]
                        hostname = None
                        try:
                            hostname = df.result()
                        except Exception:
                            pass

                        addr = f"{ip}/32"
                        ip_obj, was_created = IPAddress.objects.get_or_create(address=addr)
                        if was_created:
                            ip_obj.description = "Discovered by AutoDiscovery"
                            created += 1
                            ScanFinding.objects.create(
                                run=run,
                                summary="New IP discovered",
                                details={"ip": str(ip)}
                            )
                        else:
                            existing += 1
                            ScanFinding.objects.create(
                                run=run,
                                summary="Existing IP seen",
                                details={"ip": str(ip)}
                            )

                        if hostname:
                            try:
                                ip_obj.dns_name = hostname
                            except Exception:
                                ip_obj.description += f" Hostname={hostname}"
                            resolved += 1

                        ip_obj.save()
                        discovered.append(ip)

                # Update log progressively
                run.log = f"Scanned {checked}/{total} hosts, found {len(discovered)} alive..."
                run.save(update_fields=["log"])
                batch = []
                time.sleep(0.1)  # just to avoid log flooding

    run.stats = {"cidr": cidr, "alive": len(discovered), "created": created,
                 "existing": existing, "resolved": resolved}
    run.log += f"\nDone. Alive={len(discovered)}, Created={created}, Resolved={resolved}"
    run.save()
    return run.stats
