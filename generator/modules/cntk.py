# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source, version
from .python import Python
from .opencv import Opencv


@dependency(Python, Opencv)
@source('pip')
class Cntk(Module):

    def build(self, composer):
        return [
            r'''
            DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                openmpi-bin \
                libpng-dev \
                libtiff-dev \
                libjasper-dev''',
            r'wget --no-verbose -O - https://github.com/01org/mkl-dnn/releases/download/v0.14/mklml_lnx_2018.0.3.20180406.tgz | tar -xzf - ',
            r'cp mklml*/* /usr/local -r',
            r'wget --no-verbose -O - https://github.com/01org/mkl-dnn/archive/v0.14.tar.gz | tar -xzf -',
            r'cd mkl-dnn-0.14 && mkdir build && cd build',
            r'ln -s /usr/local external',
            r'''
            cmake -D CMAKE_BUILD_TYPE=RELEASE \
                  -D CMAKE_INSTALL_PREFIX=/usr/local \
                  ..''',
            r'make -j"$(nproc)" install',
            '',
            r'$PIP_INSTALL cntk%s' % ('' if composer.cuda_ver is None else '-gpu')
        ]
