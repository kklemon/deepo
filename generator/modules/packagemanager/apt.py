import textwrap
from . import PackageManager
from ..__module__ import dependency, source
from ..tools import Tools


@dependency(Tools)
@source('apt')
class AptitudePackageManager(PackageManager):
    def __init__(self):
        super().__init__('apt')

    def build(self, composer):
        package_names = []
        for name, version in self.packages:
            if version:
                name += '==%s' % version
            package_names.append(name)
        package_string = ' \\\n'.join(package_names)

        return [
            '''
            DEBIAN_FRONTEND=noninteractive $APT_INSTALL \\\n'''
            + textwrap.indent(package_string, '    ' * 4)
        ]
