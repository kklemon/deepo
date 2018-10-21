import textwrap
from . import PackageManager
from ..__module__ import dependency, source
from ..python import Python


@dependency(Python)
@source('pip')
class PIPPackageManager(PackageManager):
    def __init__(self):
        super().__init__('pip')

    def build(self, composer):
        package_names = []
        for name, version in self.packages:
            if version:
                name += '==%s' % version
            package_names.append(name)
        package_string = ' \\\n'.join(package_names)

        return [
            '''
            $PIP_INSTALL \ \n'''
            + textwrap.indent(package_string, '    ' * 4)
        ]
