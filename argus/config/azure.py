# Copyright 2017 Cloudbase Solutions Srl
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

"""Config options available for the Azure backend."""

from oslo_config import cfg

from argus.config import base as conf_base


class AzureOptions(conf_base.Options):

    """Config options available for the OpenStack setup."""

    def __init__(self, config):
        super(AzureOptions, self).__init__(config, group="azure")
        self._options = [
            cfg.StrOpt(
                "subscription_id", default=None,
                help="The subscription id for the Azure account"
                     "used for tests."),
            cfg.StrOpt(
                "username", default=None,
                help="The Azure account username."),
            cfg.StrOpt("password", default=None),
            cfg.StrOpt("storage_account_name", default=None),
            cfg.StrOpt("resource_group_name", default=None),
            cfg.StrOpt("resource_group_location", default=None),
            cfg.StrOpt("image_vhd_path", default=None),
            cfg.StrOpt("vm_username", default=None),
            cfg.StrOpt("vm_password", default=None),
        ]

    def register(self):
        """Register the current options to the global ConfigOpts object."""
        group = cfg.OptGroup(self.group_name, title='Azure Options')
        self._config.register_group(group)
        self._config.register_opts(self._options, group=group)

    def list(self):
        """Return a list which contains all the available options."""
        return self._options
