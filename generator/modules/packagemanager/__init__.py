from ..__module__ import dependency, source, version, Module


class PackageManager(Module):
    pms = {}

    def __init__(self, shortcut):
        super().__init__()
        self.shortcut = shortcut
        self.packages = []

    @classmethod
    def register_package_manager(cls, pm):
        cls.pms[pm.shortcut] = pm

    @classmethod
    def register_package(cls, pm_shortcut, package, version=None):
        pm = cls.pms.get(pm_shortcut)
        if not pm:
            raise Exception('\'%s\' is not a package manager.' % pm_shortcut)
        return pm.register(package, version)

    @classmethod
    def get_package_managers(cls):
        return list(pm for pm in cls.pms.values() if pm.packages)

    def register(self, package, _version=None):
        self.packages.append((package, _version))

    def name(self):
        return '%s packages' % self.shortcut


from .pip import PIPPackageManager

PackageManager.register_package_manager(PIPPackageManager())
