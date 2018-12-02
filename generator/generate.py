# -*- coding: utf-8 -*-

"""Console script for generator."""
import argparse
from core.composer import Composer
from modules.packagemanager import PackageManager


def _import(name):
    mname = name.lower()
    cname = name.title()
    mod = __import__('modules.%s' % mname, fromlist=[cname])
    mod = getattr(mod, cname)
    return mod


def main():
    """
    Generate a dockerfile according to the given modules to be installed.
    """
    parser = argparse.ArgumentParser(description='Composer')
    parser.add_argument('path')
    parser.add_argument('modules', nargs='*')
    parser.add_argument('--cuda-ver')
    parser.add_argument('--cudnn-ver')
    parser.add_argument('--join-mode', default=False)
    args = parser.parse_args()

    in_modules = []
    for module in args.modules:
        terms = module.split('==')
        version = terms[1] if len(terms) > 1 else None
        terms = terms[0].split('+')
        if len(terms) > 1:
            pm_shortcut, module = terms
            PackageManager.register_package(pm_shortcut, module, version)
        else:
            module = _import(terms[0])
            instance = module(_version=version)
            in_modules.append(instance)

    in_modules += PackageManager.get_package_managers()

    composer = Composer(in_modules, args.cuda_ver, args.cudnn_ver)
    with open(args.path, 'w') as f:
        f.write(composer.to_dockerfile(join_mode=args.join_mode))


if __name__ == "__main__":
    main()
