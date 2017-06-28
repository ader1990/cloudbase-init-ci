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
        self._name = name
        self._availability_zone = availability_zone
        self.userdata = userdata
        self.metadata = metadata
        self._username = CONFIG.local.username
        self._password = CONFIG.local.password

    def get_remote_client(self, username=None, password=None,
                          protocol='http', **kwargs):
        if username is None:
            username = self._username
        if password is None:
            password = self._password

        return windows.WinRemoteClient(self.floating_ip(),
                                       username, password,
                                       transport_protocol=protocol)

    remote_client = util.cached_property(get_remote_client, 'remote_client')

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
