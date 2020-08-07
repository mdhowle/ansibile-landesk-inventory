# ansible-landesk-inventory

LANDESK dynamic inventory plugin for Ansible

**ABANDONED**: We are transitioning away from Ivanti/LANDESK.

## Installation
See [Ansible Documentation](https://docs.ansible.com/ansible/latest/dev_guide/developing_locally.html#adding-a-plugin-locally) on installing plugins.

Requirements are `requests`.
For Kerberos authentication, `requests_kerberos` is required.
For NTLM authentication, `requests_ntlm` is required.

## Usage
See `ansible-doc -t inventory landesk` for more details.

Create a `landesk.yml` with the contents:
```
plugin: landesk
server: server.example.com
protocol: https
validate_cert: true
authentication: ntlm
username: ExampleUser
password: hunter2
query: Computer.OS.Name LIKE "%Debian%"
```

Finally, run `ansible-playbook -i landesk.yml playbook.yml`
