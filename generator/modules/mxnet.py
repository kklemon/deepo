# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source
from .python import Python


@dependency(Python)
@source('pip')
class Mxnet(Module):

    def build(self):
        if self.composer.cuda_ver is None:
            cuver = ''
        else:
            cuver = '-cu%d' % (float(self.composer.cuda_ver) * 10)

        return [
            r'''
            DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                libatlas-base-dev \
                graphviz''',
            r'''
            $PIP_INSTALL \
                mxnet%s \
                graphviz''' % cuver
        ]