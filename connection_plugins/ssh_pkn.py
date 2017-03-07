# SSH connection plugin with port knocking support
# Extends Ansible default ssh connection plugin
#
# Parameters:
#   knock_ports - list of ports to knock
#   knock_delay - delay between each knock in seconds (default 0.5 sec)
#
# Example host definition:
#   [pkn]
#   myserver ansible_host=my.server.at.example.com
#   [pkn:vars]
#   ansible_connection=ssh_pkn
#   knock_ports=[8000,9000]
#   knock_delay=2
#
# Written by Konstantin Suvorov <dev@berlic.net>
# Visit ansibledaily.com for more Ansible tricks

from ansible.plugins.connection.ssh import Connection as ConnectionSSH
from ansible.errors import AnsibleError
from socket import create_connection
from time import sleep

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class Connection(ConnectionSSH):

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)
        display.vvv("SSH_PKN (Port KNock) connection plugin is used for this host", host=self.host)

    def set_host_overrides(self, host, hostvars=None):

        if 'knock_ports' in hostvars:
            ports = hostvars['knock_ports']
            if not isinstance(ports, list):
                raise AnsibleError("knock_ports parameter for host '{}' must be list!".format(host))

            delay = 0.5
            if 'knock_delay' in hostvars:
                delay = hostvars['knock_delay']

            for p in ports:
                display.vvv("Knocking to port: {0}".format(p), host=self.host)
                try:
                    create_connection((self.host, p), 0.5)
                except:
                    pass
                display.vvv("Waiting for {0} seconds after knock".format(delay), host=self.host)
                sleep(delay)
