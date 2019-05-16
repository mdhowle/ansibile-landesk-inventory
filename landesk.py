from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: landesk
    plugin_type: inventory
    author:
        - Matthew Howle <matthew@howle.org>
    short_description: LANDESK inventory source
    requirements:
        - python >= 2.7
        - requests
    optional:
        - request_kerberos
        - requests_ntlm
    description:
        - Read inventory using LANDESK query.
        - Uses landesk.(yml|yaml) YAML configuration file to configure the inventory plugin.
    options:
        plugin:
            description: Marks this as an instance of the 'landesk' plugin.
            required: true
            choices: ['landesk']
        server:
            description: The LANDESK Core server name
            required: true
        protocol:
            description: Protocol over which to interact with the core server
            required: false
            choices: ['http', 'https']
            default: https
        validate_cert:
            description: Validate certificate if protocol is set to 'HTTPS'
            required: false
            default: true
        authentication:
            description: Authentication method to use
            choices: ['basic', 'ntlm', 'kerberos']
            default: basic
        username:
            description: Username to use if 'basic' or 'ntlm' is selected as the authentication method
            required: false
        password:
            description: Password to use if 'basic' or 'ntlm' is selected as the authentication method
        query:
            description: LANDESK BNF query for machines
            required: true
"""

EXAMPLES = r"""
# Minimal example.
plugin: landesk
server: landesk.example.com
query: Computer.OS.Name LIKE "%Debian%"

# Example with all values assigned
plugin: landesk
server: dc.example.com
protocol: https
validate_cert: true
authentication: ntlm
username: ExampleUser
password: "SecurePassword"
query: Computer.OS.Name LIKE "%Debian%"
"""

import xml.etree.ElementTree as ET

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin


try:
    import requests
except ImportError:
    raise AnsibleError("The LANDESK dynamic inventory plugin requires 'requests' library")

try:
    from requests_kerberos import HTTPKerberosAuth
    HAS_REQKRB_AUTH = True
except ImportError:
    HAS_REQKRB_AUTH = False

try:
    from requests_ntlm import HttpNtlmAuth as HTTPNTLMAuth
    HAS_REQNTLM_AUTH = True
except ImportError:
    HAS_REQKRB_AUTH = False


class InventoryModule(BaseInventoryPlugin):
    NAME = 'landesk'

    def __init__(self):
        super(InventoryModule, self).__init__()

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            filenames = ('landesk.yaml', 'landesk.yml')
            return any((path.endswith(filename) for filename in filenames))
        return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self.config_data = self._read_config_data(path)

        auth_type = self.get_option("authentication")

        if auth_type in ("basic", "ntlm"):
            username = self.get_option("username")
            password = self.get_option("password")

            if not (username and password):
                raise AnsibleError(
                    ("Username and password are required for "
                    "{} authentication.").format(auth_type)
                )
            if auth_type == "basic":
                self._auth = (username, password)
            elif auth_type == "ntlm":
                if HAS_REQNTLM_AUTH:
                    self._auth = HTTPNTLMAuth(username, password)
                else:
                    raise AnsibleError("The library 'requests_ntlm' is required for "
                                       "NTLM authentication.")

        elif auth_type == "kerberos":
            if HAS_REQKRB_AUTH:
                self._auth = HTTPKerberosAuth()
            else:
                raise AnsibleError("The library 'requests_kerberos' is required for "
                                   "Kerberos authentication.")

        self._build_inventory()

    def _build_inventory(self):
        server = self.get_option("server")
        protocol = self.get_option("protocol")
        query = self.get_option("query")

        if protocol == "https":
            validate_cert = self.get_option("validate_cert")
            if not validate_cert:
                import urllib3
                urllib3.disable_warnings()
        else:
            validate_cert = False

        endpoint = "{}://{}/mbsdkservice/msgsdk.asmx/ListMachines".format(
                protocol, server
        )

        payload = {"Filter": query}
        result = requests.get(endpoint, params=payload, verify=validate_cert,
                              auth=self._auth)

        result.raise_for_status()

        data = result.text

        root = ET.fromstring(data)

        namespaces = {
            "ld": "http://landesk.com/MBSDKService/MBSDK/"
        }

        for device_node in root.findall("./ld:Devices/ld:Device", namespaces):
            name_tag = device_node.find("ld:DeviceName", namespaces)
            host = name_tag.text
            self.inventory.add_host(host) 
