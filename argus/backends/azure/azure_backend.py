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
import six

from argus.backends import base
from argus.backends import windows
from argus.backends.azure import client as azure_client

from argus import config as argus_config
from argus import log as argus_log

CONFIG = argus_config.CONFIG

RETRY_COUNT = 50
RETRY_DELAY = 10

LOG = argus_log.LOG


# pylint: disable=abstract-method
@six.add_metaclass(abc.ABCMeta)
class BaseAzureBackend(base.CloudBackend):
    """A back-end which uses Azure as the driving core."""

    def __init__(self, name=None, userdata=None, metadata=None,
                 availability_zone=None):
        super(BaseAzureBackend, self).__init__(
            name=name, userdata=userdata, metadata=metadata,
            availability_zone=availability_zone)
        self._azure_client = azure_client.AzureClient(
            CONFIG.azure.subscription_id,
            CONFIG.azure.username,
            CONFIG.azure.password,
            CONFIG.azure.resource_group_name,
            CONFIG.azure.storage_account_name,
            CONFIG.azure.resource_group_location,
            CONFIG.azure.image_vhd_path,
            CONFIG.azure.vm_username,
            CONFIG.azure.vm_password)

    def setup_instance(self):
        super(BaseAzureBackend, self).setup_instance()
        LOG.info("Creating Azure resource group")
        self._azure_client.create_resource_group()
        LOG.info("Creating Azure storage account")
        self._azure_client.create_storage_account()
        LOG.info("Creating Azure VM")
        self._azure_client.create_vm()

    def cleanup(self):
        LOG.info("Destroying Azure VM")
        self._azure_client.destroy_vm()

    def internal_instance_id(self):
        """Get the underlying instance ID.

        Gets the instance ID depending on the internals of the back-end.
        """
        return self._azure_client.vm_name

    def floating_ip(self):
        """Get the underlying floating IP."""
        floating_ip = self._azure_client.get_floating_ip()
        LOG.info("Floating ip is {}".format(floating_ip))
        return floating_ip

    def instance_output(self, limit=6500):
        """Get the console output, sent from the instance."""
        return ""

    def reboot_instance(self):
        """Reboot the underlying instance."""
        pass

    def instance_password(self):
        """Get the underlying instance password, if any."""
        return self._azure_client.vm_password

    def private_key(self):
        """Get the underlying private key."""
        pass

    def public_key(self):
        """Get the underlying public key."""
        pass

    def instance_server(self):
        """Get the instance server object."""
        return {
            'name': self._azure_client.vm_name,
            'id': self._azure_client.vm_name
        }

    def get_image_by_ref(self):
        """Get the image object by its reference id."""
        return {
            'image': {
                'OS-EXT-IMG-SIZE:size': self._azure_client.vm_disk_size
            }
        }


class WindowsAzureBackend(windows.WindowsBackendMixin, BaseAzureBackend):
    """Azure back-end tailored to work with Windows platforms."""
