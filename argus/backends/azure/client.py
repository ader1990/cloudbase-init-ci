# Copyright 2017 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import abc
import random
import six

from argus import util
from azure.common.credentials import UserPassCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

PROVISIONING_STATE_CREATING = 'Creating'


@six.add_metaclass(abc.ABCMeta)
class BaseAzureClient(object):
    """Class for managing Azure instances

    """
    def __init__(self, subscription_id=None, username=None, password=None,
                 resource_group_name=None, storage_account_name=None,
                 availability_zone=None, image_vhd_path=None, vm_username=None,
                 vm_password=None):
        self.vm_disk_size = 50000
        self._subscription_id = subscription_id
        self._username = username
        self._password = password
        self._resource_group_name = resource_group_name
        self._storage_account_name = storage_account_name
        self._availability_zone = availability_zone
        self._image_vhd_path = image_vhd_path
        self._vm_username = vm_username
        self.vm_password = vm_password
        self._creds = UserPassCredentials(username, password)
        self.res_client = ResourceManagementClient(
            self._creds, subscription_id)
        self._stor_client = StorageManagementClient(
            self._creds, subscription_id)
        self._vm_client = ComputeManagementClient(
            self._creds, subscription_id)
        self.net_client = NetworkManagementClient(
            self._creds, subscription_id)

    @abc.abstractmethod
    def create_vm(self):
        pass

    @abc.abstractmethod
    def destroy_vm(self):
        pass

    @abc.abstractmethod
    def create_resource_group(self):
        pass

    @abc.abstractmethod
    def create_storage_account(self):
        pass

    @abc.abstractmethod
    def create_nic(self):
        pass

    @abc.abstractmethod
    def get_floating_ip(self):
        pass

    @abc.abstractmethod
    def get_vm_state(self):
        pass


class AzureClient(BaseAzureClient):
    """Class for managing Azure instances
    """
    def __init__(self, subscription_id=None, username=None, password=None,
                 resource_group_name=None, storage_account_name=None,
                 availability_zone=None, image_vhd_path=None,
                 vm_username=None, vm_password=None):
        super(AzureClient, self).__init__(
            subscription_id, username, password, resource_group_name,
            storage_account_name, availability_zone, image_vhd_path,
            vm_username, vm_password)

        self.vm_name = "argusvm-" + AzureClient._get_random_id()
        self._os_disk_name = "argusdisk-" + AzureClient._get_random_id()
        self._vnet_name = "argusvnet-" + AzureClient._get_random_id()
        self._sub_net_name = "argussubnet-" + AzureClient._get_random_id()
        self._nic_name = "argusnic-" + AzureClient._get_random_id()
        self._vip_name = "argusvip-" + AzureClient._get_random_id()
        self._ip_config_name = "argusip-" + AzureClient._get_random_id()
        self._sec_group_name = 'argussecgrp-' + AzureClient._get_random_id()

    @staticmethod
    def _get_random_id():
        return str(random.randint(0, 10000))

    def create_vm(self):
        nic = self.create_nic()
        vm_parameters = self._create_vm_parameters(
            self.vm_name, self._vm_username, self.vm_password,
            self._os_disk_name, nic.id)
        self._vm_client.virtual_machines.create_or_update(
            self._resource_group_name, self.vm_name,
            vm_parameters)

        self._vm_client.virtual_machines.start(
            self._resource_group_name, self.vm_name)

    def destroy_vm(self):
        self._vm_client.virtual_machines.delete(
            self._resource_group_name, self.vm_name).result()
        self.net_client.network_interfaces.delete(
            self._resource_group_name, self._nic_name).result()
        self.net_client.virtual_networks.delete(
            self._resource_group_name, self._vnet_name).result()
        self.net_client.network_security_groups.delete(
            self._resource_group_name, self._sec_group_name).result()
        self.net_client.public_ip_addresses.delete(
            self._resource_group_name, self._vip_name).result()

    def create_resource_group(self):
        self.res_client.resource_groups.create_or_update(
            self._resource_group_name,
            {
                'location': self._availability_zone
            })

    def create_storage_account(self):
        async_create = self._stor_client.storage_accounts.create(
            self._resource_group_name,
            self._storage_account_name,
            {
                'location': self._availability_zone,
                'sku': {'name': 'standard_lrs'},
                'kind': 'storage'
            })
        async_create.wait()

    def create_security_group_rule(self, sec_group_name,
                                   rule_name, port, priority, direction):
        self.net_client.security_rules.create_or_update(
            self._resource_group_name,
            sec_group_name, rule_name,
            {
                'access': 'allow',
                'protocol': 'Tcp',
                'direction': direction,
                'source_address_prefix': '*',
                'destination_address_prefix': '*',
                'source_port_range': '*',
                'destination_port_range': port,
                'priority': priority
            }).wait()

    def create_nic(self):
        """Create a Network Interface for a VM.
        """

        # pylint: disable=maybe-no-member
        sec_gr_id = self.net_client.network_security_groups.create_or_update(
            self._resource_group_name,
            self._sec_group_name,
            {
                'location': self._availability_zone
            }).result().id
        self.create_security_group_rule(
            self._sec_group_name, 'secgrrule-1', '3389', 100, 'inbound')
        self.create_security_group_rule(
            self._sec_group_name, 'secgrrule-2', '5985', 101, 'inbound')
        self.create_security_group_rule(
            self._sec_group_name, 'secgrrule-3', '5986', 102, 'inbound')
        self.create_security_group_rule(
            self._sec_group_name, 'secgrrule-4', '*', 103, 'outbound')
        self.net_client.virtual_networks.create_or_update(
            self._resource_group_name,
            self._vnet_name,
            {
                'location': self._availability_zone,
                'address_space': {
                    'address_prefixes': ['10.0.0.0/16']
                }
            }).wait()

        # pylint: disable=maybe-no-member
        subnet_id = self.net_client.subnets.create_or_update(
            self._resource_group_name,
            self._vnet_name,
            self._sub_net_name,
            {
                'address_prefix': '10.0.0.0/24',
                'network_security_group':
                {
                    'id': sec_gr_id
                }
            }).result().id

        # pylint: disable=maybe-no-member
        vip_id = self.net_client.public_ip_addresses.create_or_update(
            self._resource_group_name,
            self._vip_name,
            {
                'location': self._availability_zone,
                'public_ip_allocation_method': 'dynamic'
            }).result().id

        return self.net_client.network_interfaces.create_or_update(
            self._resource_group_name,
            self._nic_name,
            {
                'location': self._availability_zone,
                'ip_configurations': [{
                    'name': self._ip_config_name,
                    'subnet': {
                        'id': subnet_id
                    },
                    'public_ip_address': {
                        'id': vip_id
                    },
                }]
            }).result()

    def _create_vm_parameters(self, vm_name, vm_username, vm_password,
                              os_disk_name, nic_id):
        """Create the VM parameters structure.
        """
        vhd_uri = 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
            self._storage_account_name, vm_name)
        return {
            'location': self._availability_zone,
            'os_profile': {
                'computer_name': vm_name,
                'admin_username': vm_username,
                'admin_password': vm_password
            },
            'hardware_profile': {
                'vm_size': 'Standard_D1_v2'
            },
            'storage_profile': {
                'os_disk': {
                    'name': os_disk_name,
                    'os_type': 'Windows',
                    'image': {'uri': self._image_vhd_path},
                    'caching': 'None',
                    'create_option': 'fromImage',
                    'vhd': {
                        'uri': vhd_uri
                    }
                }
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': nic_id,
                }]
            },
        }

    @util.retry_on_error(max_attempts=30, sleep_seconds=8)
    def get_floating_ip(self):
        # pylint: disable=maybe-no-member
        vm_state = self.get_vm_state()
        if vm_state != PROVISIONING_STATE_CREATING:
            raise Exception('VM is not in creating state')
        floating_ip = self.net_client.public_ip_addresses.get(
            self._resource_group_name, self._vip_name).ip_address
        if not floating_ip:
            raise Exception('Floating IP not available')
        return floating_ip

    @util.retry_on_error(max_attempts=5, sleep_seconds=5)
    def get_vm_state(self):
        # pylint: disable=maybe-no-member
        return self._vm_client.virtual_machines.get(
            self._resource_group_name, self.vm_name).provisioning_state
