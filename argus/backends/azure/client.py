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
from azure.storage import CloudStorageAccount

VM_REFERENCE = {
    'windows': {
        'publisher': 'MicrosoftWindowsServerEssentials',
        'offer': 'WindowsServerEssentials',
        'sku': 'WindowsServerEssentials',
        'version': 'latest'
    }
}

@six.add_metaclass(abc.ABCMeta)
class BaseAzureClient(object):
    """Class for managing Azure instances

    """
    def __init__(self, subscription_id=None, username=None, password=None,
                 resource_group_name=None, storage_account_name=None,
                 availability_zone=None, image_vhd_path=None, vm_username=None,
                 vm_password=None):
        self._subscription_id = subscription_id
        self._username = username
        self._password = password
        self._resource_group_name = resource_group_name
        self._storage_account_name = storage_account_name
        self._availability_zone = availability_zone
        self._image_vhd_path = image_vhd_path
        self._vm_username = vm_username
        self._vm_password = vm_password
        self._credentials = UserPassCredentials(username, password)
        self._resource_client = ResourceManagementClient(self._credentials, subscription_id)
        self._storage_client = StorageManagementClient(self._credentials, subscription_id)
        self._compute_client = ComputeManagementClient(self._credentials, subscription_id)
        self._network_client = NetworkManagementClient(self._credentials, subscription_id)

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


class AzureClient(BaseAzureClient):
    """Class for managing Azure instances

    """
    def __init__(self, subscription_id=None, username=None, password=None,
                 resource_group_name=None, storage_account_name=None,
                 availability_zone=None, image_vhd_path=None, vm_username=None,
                 vm_password=None):
        super(AzureClient, self).__init__(subscription_id, username,
            password, resource_group_name, storage_account_name, availability_zone,
            image_vhd_path, vm_username, vm_password)

        self._vm_name = "argusvm-" + str(random.randint(0,10000))
        self._os_disk_name = "argusdisk-" + str(random.randint(0,10000))
        self._vnet_name = "argusvnet-" + str(random.randint(0,10000))
        self._sub_net_name = "argussubnet-" + str(random.randint(0,10000))
        self._nic_name = "argusnic-" + str(random.randint(0,10000))
        self._vip_name = "argusvip-" + str(random.randint(0,10000))
        self._ip_config_name = "argusip-" + str(random.randint(0,10000))
        self._sec_group_name = 'argussecgrp-' + str(random.randint(0,10000))

    def create_vm(self):
        nic = self.create_nic()
        vm_parameters = self._create_vm_parameters(self._vm_name, self._vm_username,
            self._vm_password, self._os_disk_name, nic.id, VM_REFERENCE['windows'])
        async_vm_creation = self._compute_client.virtual_machines.create_or_update(
            self._resource_group_name, self._vm_name, vm_parameters)

        async_vm_start = self._compute_client.virtual_machines.start(
            self._resource_group_name, self._vm_name)

    def destroy_vm(self):
         self._compute_client.virtual_machines.delete(self._resource_group_name, self._instance_name).result()
         self._network_client.network_interfaces.delete(self._resource_group_name, self._nic_name).result()
         self._network_client.network_security_groups.delete(self._resource_group_name, self._sec_group_name).result()
         self._network_client.virtual_networks.delete(self._resource_group_name, self._vnet_name).result()
         self._network_client.public_ip_addresses.delete(self._resource_group_name, self._vip_name).result()

    def create_resource_group(self):
        self._resource_client.resource_groups.create_or_update(
            self._resource_group_name,
            {
                'location': self._availability_zone
            })

    def create_storage_account(self):
        async_create = self._storage_client.storage_accounts.create(
            self._resource_group_name,
            self._storage_account_name,
            {
                'location': self._availability_zone,
                'sku': {'name': 'standard_lrs'},
                'kind': 'storage'
            })
        async_create.wait()

    def create_nic(self):
        """Create a Network Interface for a VM.
        """

        async_secgroup_creation = self._network_client.network_security_groups.create_or_update(
            self._resource_group_name, self._sec_group_name, {'location':self._availability_zone})
        secgroup_info = async_secgroup_creation.result()
        
        self._network_client.security_rules.create_or_update(self._resource_group_name, self._sec_group_name, 'secgr1', {'access':'allow', 'protocol':'Tcp', 'direction':'inbound', 'source_address_prefix':'*','destination_address_prefix':'*', 'source_port_range':'*', 'destination_port_range':'3389', 'priority':100}).wait()
        self._network_client.security_rules.create_or_update(self._resource_group_name, self._sec_group_name, 'secgr4', {'access':'allow', 'protocol':'Tcp', 'direction':'inbound', 'source_address_prefix':'*','destination_address_prefix':'*', 'source_port_range':'*', 'destination_port_range':'5985', 'priority':101}).wait()
        self._network_client.security_rules.create_or_update(self._resource_group_name, self._sec_group_name, 'secgr3', {'access':'allow', 'protocol':'Tcp', 'direction':'inbound', 'source_address_prefix':'*','destination_address_prefix':'*', 'source_port_range':'*', 'destination_port_range':'5986', 'priority':102}).wait()
        self._network_client.security_rules.create_or_update(self._resource_group_name, self._sec_group_name, 'secgr2', {'access':'allow', 'protocol':'Tcp', 'direction':'outbound', 'source_address_prefix':'*','destination_address_prefix':'*', 'source_port_range':'*', 'destination_port_range':'*', 'priority':103}).wait()

        async_vnet_creation = self._network_client.virtual_networks.create_or_update(
           self._resource_group_name,
           self._vnet_name,
           {
                'location': self._availability_zone,
                'address_space': {
                    'address_prefixes': ['10.0.0.0/16']
                }
           })
        async_vnet_creation.wait()

        async_subnet_creation = self._network_client.subnets.create_or_update(
            self._resource_group_name,
            self._vnet_name,
            self._sub_net_name,
            {
                'address_prefix': '10.0.0.0/24',
                'network_security_group' : {'id' : secgroup_info.id}
            })
        subnet_info = async_subnet_creation.result()
        
        async_vip_creation = self._network_client.public_ip_addresses.create_or_update(
            self._resource_group_name,
            self._vip_name,
            {
                'location': self._availability_zone,
                'public_ip_allocation_method':'dynamic'
            }
        )
        vip_info = async_vip_creation.result()

        async_nic_creation = self._network_client.network_interfaces.create_or_update(
            self._resource_group_name,
            self._nic_name,
            {
                'location': self._availability_zone,
                'ip_configurations': [{
                    'name':self._ip_config_name,
                    'subnet': {
                        'id': subnet_info.id
                    },
                    'public_ip_address': {
                        'id': vip_info.id
                    },
                 }]
            })
        return async_nic_creation.result()
    
    def _create_vm_parameters(self, vm_name, vm_username, vm_password, os_disk_name, nic_id, vm_reference):
        """Create the VM parameters structure.
        """
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
                    'uri': 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
                        self._storage_account_name, vm_name)
                }
            },
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        },
        }
    @util.retry_on_error(max_attempts=20, sleep_seconds=5)
    def get_floating_ip(self):
        floating_ip = self._network_client.public_ip_addresses.get(self._resource_group_name, self._vip_name).ip_address
        if not floating_ip:
            raise Exception('Floating IP not available')
        return floating_ip
