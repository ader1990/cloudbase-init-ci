# Copyright 2015 Cloudbase Solutions Srl
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


from argus.scenarios import base


class CloudScenario(base.BaseScenario):
    """Base scenario class for testing cloudbaseinit."""

    service_type = 'http'

    @classmethod
    def prepare_recipe(cls):
        """Prepare the underlying recipe using custom behavior tailored to cloudbaseinit."""
        return cls.recipe.prepare(service_type=cls.service_type)
