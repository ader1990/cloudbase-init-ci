from argus.backends import base as base_backend
from argus.backends import windows as windows_backend
from argus.client import windows
from argus import config as argus_config
from argus import log as argus_log
from argus import util

CONFIG = argus_config.CONFIG


class LocalBackend(windows_backend.WindowsBackendMixin,
                   base_backend.BaseBackend,
                   windows_backend.BaseMetadataProviderMixin):
    """ Local Backend for testing Windows machines
        that are already installed and ready"""
    def __init__(self, name=None, userdata=None, metadata=None,
                 availability_zone=None):
        super(LocalBackend, self).__init__(name=name, userdata=userdata,
                                           metadata=metadata,
                                           availability_zone=availability_zone)
        self._username = CONFIG.local.username
        self._password = CONFIG.local.password

    def get_remote_client(self, protocol='http', **kwargs):
        super(LocalBackend, self).get_remote_client(self._username,
                                                    self._password,
                                                    protocol, **kwargs)

    def setup_instance(self):
        pass

    def cleanup(self):
        pass

    def save_instance_output(self):
        pass

    def get_password(self):
        return lambda: self._password

    def get_username(self):
        return lambda: self._username

    @property
    def floating_ip(self):
        return lambda: CONFIG.local.ip
