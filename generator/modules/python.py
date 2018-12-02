# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source, version
from .tools import Tools


@dependency(Tools)
@version('3.5')
@source('apt')
class Python(Module):

    def __init__(self, **args):
        super(self.__class__, self).__init__(**args)
        if self.version not in ('2.7', '3.5', '3.6',):
            raise NotImplementedError('unsupported python version')

    def build(self, composer):
        if self.version == '3.5':
            stmts = [
                r'''
                DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                    python3-pip \
                    python3-dev''',
                r'ln -s /usr/bin/python3 /usr/local/bin/python',
                r'pip3 --no-cache-dir install --upgrade pip',
                r'$PIP_INSTALL setuptools'
            ]
        elif self.version == '3.6':
            stmts = [
                r'''
                DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                    software-properties-common''',
                r'add-apt-repository ppa:deadsnakes/ppa',
                r'apt-get update',
                r'''
                DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                    python3.6 \
                    python3.6-dev''',
                r'''
                wget -O ~/get-pip.py \
                    https://bootstrap.pypa.io/get-pip.py''',
                r'python3.6 ~/get-pip.py',
                r'ln -s /usr/bin/python3.6 /usr/local/bin/python3',
                r'ln -s /usr/bin/python3.6 /usr/local/bin/python',
                r'$PIP_INSTALL setuptools']
        else:
            stmts = [
                r'''
                DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                    python-pip \
                    python-dev''',
                r'''
                $PIP_INSTALL \
                    setuptools \
                    pip''']
        stmts.append(r'''
            $PIP_INSTALL \
                numpy \
                scipy \
                pandas \
                cloudpickle \
                scikit-learn \
                matplotlib \
                Cython''')
        return stmts
