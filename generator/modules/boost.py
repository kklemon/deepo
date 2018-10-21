# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source
from .tools import Tools
from .python import Python


@dependency(Tools, Python)
@source('src')
class Boost(Module):

    def __repr__(self):
        return ''

    def build(self, composer):
        pyver = composer.ver(Python)
        if pyver == '2.7':
            return [
                r'''
                DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                    libboost-all-dev
                '''
            ]
        return [
            r'wget -O ~/boost.tar.gz '
            r'https://dl.bintray.com/boostorg/release/1.65.1'
            r'/source/boost_1_65_1.tar.gz',
            r'tar -zxf ~/boost.tar.gz -C ~',
            r'cd ~/boost_*',
            r'./bootstrap.sh --with-python=python%s' % pyver,
            r'./b2 install --prefix=/usr/local'
        ]
