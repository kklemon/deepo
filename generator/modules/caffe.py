# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source
from .tools import Tools
from .boost import Boost
from .python import Python
from .opencv import Opencv


@dependency(Tools, Python, Boost, Opencv)
@source('git')
class Caffe(Module):

    def build(self, composer):
        pyver = composer.ver(Python)
        cpu_only = composer.cuda_ver is None

        stmts = [
            r'$GIT_CLONE https://github.com/BVLC/caffe ~/caffe',
            r'cp ~/caffe/Makefile.config.example ~/caffe/Makefile.config',
            r"sed -i 's/# %s/%s/g' ~/caffe/Makefile.config"
            % (('CPU_ONLY', 'CPU_ONLY') if cpu_only else ('USE_CUDNN', 'USE_CUDNN'))
        ]

        if pyver != '2.7':
            stmts += [
                r"sed -i 's/# PYTHON_LIBRARIES/PYTHON_LIBRARIES/g' "
                r'~/caffe/Makefile.config',
            ]

        stmts += [
            r"sed -i 's/# WITH_PYTHON_LAYER/WITH_PYTHON_LAYER/g' "
            r'~/caffe/Makefile.config',
            r"sed -i 's/# OPENCV_VERSION/OPENCV_VERSION/g' "
            r'~/caffe/Makefile.config'
        ]

        if not cpu_only:
            stmts += [
                r"sed -i 's/# USE_NCCL/USE_NCCL/g' ~/caffe/Makefile.config",
                r"sed -i 's/-gencode arch=compute_20,code=sm_20//g' ~/caffe/Makefile.config",
                r"sed -i 's/-gencode arch=compute_20,code=sm_21//g' ~/caffe/Makefile.config"
            ]

        if pyver == '3.5':
            stmts += [r"sed -i 's/2\.7/3\.5/g' ~/caffe/Makefile.config"]
        elif pyver == '3.6':
            stmts += [
                r"sed -i 's/2\.7/3\.6/g' ~/caffe/Makefile.config",
                r"sed -i 's/3\.5/3\.6/g' ~/caffe/Makefile.config",
            ]

        return stmts + [
            r"sed -i 's/\/usr\/lib\/python/\/usr\/local\/lib\/python/g' "
            r"~/caffe/Makefile.config",
            r"sed -i 's/\/usr\/local\/include/\/usr\/local\/include "
            r"\/usr\/include\/hdf5\/serial/g' ~/caffe/Makefile.config",
            r"sed -i 's/hdf5/hdf5_serial/g' ~/caffe/Makefile",
            r'cd ~/caffe',
            r'make -j"$(nproc)" -Wno-deprecated-gpu-targets distribute',
            '',
            r'''
            # fix ValueError caused by python-dateutil 1.x
            sed -i 's/,<2//g' ~/caffe/python/requirements.txt
            ''',
            '',
            r'$PIP_INSTALL -r ~/caffe/python/requirements.txt',
            '',
            r'cd ~/caffe/distribute/bin',
            r'for file in *.bin; do mv "$file" "${file%%%%.bin}"; done',
            '',
            r'cd ~/caffe/distribute',
            r'cp -r bin include lib proto /usr/local/',
            r'cp -r python/caffe /usr/local/lib/python%s/dist-packages/' % pyver
        ]
