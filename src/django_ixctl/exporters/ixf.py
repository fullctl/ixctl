import datetime
import json


def export(ix, pretty=False):
    member_list = []
    ixp_list = []

    rv = {
        "version": "0.6",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "member_list": member_list,
        "ixp_list": [{"ixp_id": ix.pdb.id, "shortname": ix.name}],
    }

    for ix in [ix]:
        asns = []
        for member in ix.member_set.all():
            if member.asn in asns:
                continue
            connection_list = []
            member_dict = {
                "asnum": member.asn,
                "member_type": member.ixf_member_type,
                "connection_list": connection_list,
            }
            member_list.append(member_dict)
            asns.append(member.asn)
            for _member in ix.member_set.filter(asn=member.asn):
                vlan_list = [{}]
                connection = {
                    "ixp_id": _member.ix.id,
                    "state": _member.ixf_state,
                    "if_list": [{"if_speed": _member.speed}],
                    "vlan_list": vlan_list,
                }
                connection_list.append(connection)

                if _member.ipaddr4:
                    vlan_list[0]["ipv4"] = {
                        "address": "{}".format(_member.ipaddr4),
                        "routeserver": _member.is_rs_peer,
                    }
                if _member.ipaddr6:
                    vlan_list[0]["ipv6"] = {
                        "address": "{}".format(_member.ipaddr6),
                        "routeserver": _member.is_rs_peer,
                    }

    if pretty:
        return json.dumps(rv, indent=2)
    else:
        return json.dumps(rv)
