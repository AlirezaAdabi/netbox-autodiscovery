from netbox.plugins import PluginConfig

class AutoDiscoveryConfig(PluginConfig):
    name = "netbox_autodiscovery"
    verbose_name = "Auto Discovery"
    description = "Scan IP ranges or Cisco devices and import results into NetBox"
    version = "0.1"
    base_url = "autodiscovery"
    min_version = "4.0.0"

config = AutoDiscoveryConfig
