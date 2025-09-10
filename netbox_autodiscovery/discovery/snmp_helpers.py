# netbox_autodiscovery/discovery/snmp_helpers.py
from pysnmp.hlapi import (
    getCmd,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    nextCmd,
    SnmpEngine,
)


def snmp_get(host, community, oid, port=161):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port), timeout=1, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
    if errorIndication or errorStatus:
        return None
    for varBind in varBinds:
        return str(varBind[1])
    return None


def snmp_walk(host, community, oid, port=161):
    results = {}
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port), timeout=1, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False,
    ):
        if errorIndication or errorStatus:
            break
        for varBind in varBinds:
            oid_str, val = varBind
            idx = oid_str.prettyPrint().split(".")[-1]
            results[idx] = str(val)
    return results
