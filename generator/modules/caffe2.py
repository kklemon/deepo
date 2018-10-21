# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source
from .tools import Tools
from .python import Python
from .opencv import Opencv


@dependency(Tools, Python, Opencv)
@source('git')
class Caffe2(Module):

    def build(self):
        switcher = 'OFF' if self.composer.cuda_ver is None else 'ON'
        pyver = self.composer.ver(Python)
        if pyver == '3.5':
            platform = 'cp35-cp35'
        elif pyver == '3.6':
            platform = 'cp36-cp36m'
        else:
            platform = 'cp27-cp27mu'

        if self.composer.cuda_ver is None:
            cuver = 'cpu'
        else:
            cuver = 'cu%d' % (float(self.composer.cuda_ver) * 10)

        stmts = [
            r'''
            DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                libprotobuf-dev \
                protobuf-compiler''',
            '',
            r'''
            $PIP_INSTALL \
                future \
                numpy \
                protobuf \
                enum34 \
                pyyaml \
                typing''',
        ]

        if cuver in ['cu90'] and platform in ['cp27-cp27mu', 'cp36-cp36m']:
            stmts += [
                r'''
                wget -O ~/caffe2.tar.xz \
                    https://github.com/ufoym/prebuild/raw/caffe2/caffe2      -master-%s-%s-linux_x86_64.tar.xz
                ''' % (cuver, platform),
                r'tar -xvf ~/caffe2.tar.xz -C /usr/local/lib'
            ]
        else:
            stmts += [
                r'''
                $GIT_CLONE https://github.com/pytorch/pytorch.git \
                    ~/caffe2 --branch master --recursive''',
                r'cd ~/caffe2 && mkdir build && cd build',
                r'''
                cmake -D CMAKE_BUILD_TYPE=RELEASE \
                      -D CMAKE_INSTALL_PREFIX=/usr/local \
                      -D USE_CUDA=%s \
                      -D USE_MPI=OFF \
                      -D USE_NNPACK=OFF \
                      -D USE_ROCKSDB=OFF \
                      -D BUILD_TEST=OFF \
                      ..''' % switcher,
                r'make -j"$(nproc)" install'
            ]
        return stmts
