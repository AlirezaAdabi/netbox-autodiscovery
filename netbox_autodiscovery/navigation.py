from netbox.plugins import PluginMenu, PluginMenuItem

menu_items = [
    PluginMenuItem(link="plugins:netbox_autodiscovery:scanner_list", link_text="Scanners"),
    PluginMenuItem(link="plugins:netbox_autodiscovery:scanrun_list", link_text="Runs"),
]

menu = PluginMenu(
    label="Auto Discovery",
    groups=(("Resources", menu_items),),
)
