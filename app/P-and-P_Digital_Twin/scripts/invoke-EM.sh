curl --location 'http://192.168.130.51:8000/xml-scheme/' --header 'Content-Type: application/json' --data '{
    "CyberAttack": {
        "Type": "Denial of Service",
        "Vector": {
            "attack_timestamp": "2024-09-07T16:08:44.613Z",
            "attack_location": "DNS server",
            "Asset_IPAddress": "192.168.0.200"
        }
    },
    "OrganizationAssets": {
        "Asset_IPAddress": "192.168.0.200.",
        "Asset_name": "Server",
        "Asset_Type": "primary"
        },
    "ThreatActor": {
        "ThreatActor_IPAddress": "abc",
        "ThreatActor_Group": "internal_test",
        "ThreatActor_Technique": "Volumatric",
        "ThreatActor_Intension": "unavailable_service"
        },
    "TTP": {
        "Tactics": "a",
        "Techniques": "b",
        "Procedure": "c"
        },
    "Vulnerability": {
        "Source": "a",
        "Destination": "b",
        "Timestamp": "c"
        }
    }
'
