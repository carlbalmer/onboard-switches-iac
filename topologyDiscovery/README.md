switch_discovery/
├── discovery/                        # All discovery logic per vendor
│   ├── __init__.py
│   ├── HirschmannDiscovery.py
│   ├── LantechDiscovery.py
│   ├── KontorDiscovery.py
│   ├── NomadDiscovery.py
│   └── BaseDiscovery.py             # Abstract base class for all discovery types
│
├── TopologyDiscovery.py             # Recursive discovery (builds full graph)
├── StartDiscovery.py                # Entry point to launch from seed IP
├── ssh_client.py                    # Shared SSH utility
├── credentials.yaml                 # Default credentials per vendor
├── data_model.py                    # Normalized switch data structure
├── README.md
└── output/
    └── inventory.yaml               # Output file with discovered switches