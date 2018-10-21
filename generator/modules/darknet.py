# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source
from .tools import Tools


@dependency(Tools)
@source('git')
class Darknet(Module):

    def build(self):
        use_gpu = 1 if self.composer.cuda_ver else 0

        return [
            r'$GIT_CLONE https://github.com/pjreddie/darknet.git ~/darknet',
            r'cd ~/darknet',
            r"sed -i 's/GPU=0/GPU=%d/g' ~/darknet/Makefile" % use_gpu,
            r"sed -i 's/CUDNN=0/CUDNN=%d/g' ~/darknet/Makefile" % use_gpu,
            r'make -j"$(nproc)"',
            r'cp ~/darknet/include/* /usr/local/include',
            r'cp ~/darknet/*.a /usr/local/lib',
            r'cp ~/darknet/*.so /usr/local/lib',
            r'cp ~/darknet/darknet /usr/local/bin'
        ]
