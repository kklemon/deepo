# -*- coding: utf-8 -*-
from .__module__ import Module, dependency, source
from .tools import Tools


@dependency(Tools)
@source('git')
class Torch(Module):

    def build(self, composer):
        stmts = [
            r'export TORCH_NVCC_FLAGS="-D__CUDA_NO_HALF_OPERATORS__"',
            r'$GIT_CLONE https://github.com/torch/distro.git ~/torch'
            r' --recursive',
            r'cd ~/torch/exe/luajit-rocks',
            r'mkdir build && cd build',
            r'''
            cmake -D CMAKE_BUILD_TYPE=RELEASE \
                  -D CMAKE_INSTALL_PREFIX=/usr/local \
                  -D WITH_LUAJIT21=ON \
                  ..
            ''',
            r'make -j"$(nproc)" install'
            '',
            r'''
            DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
                libjpeg-dev \
                libpng-dev \
                libreadline-dev''',
            r'$GIT_CLONE https://github.com/Yonaba/Moses ~/moses',
            r'cd ~/moses',
            r'luarocks install rockspec/moses-1.6.1-1.rockspec',
            '',
            r'cd ~/torch',
            r"sed - i 's/extra\/cudnn/extra\/cudnn \&\& git checkout R7/' install.sh",
            r'''
            sed -i 's/$PREFIX\/bin\/luarocks/luarocks/' install.sh && \
            sed -i '/qt/d' install.sh && \
            sed -i '/Installing Lua/,/^cd \.\.$/d' install.sh && \
            sed -i '/path_to_nvidiasmi/,/^fi$/d' install.sh && \
            sed -i '/Restore anaconda/,/^Not updating$/d' install.sh && \
            sed -i '/You might want to/,/^fi$/d' install.sh
            ''',
        ]

        if composer.cuda_ver is None:
            stmts += [r'''sed -i 's/\[ -x "$path_to_nvcc" \]/false/' install.sh''']

        return stmts + [
            '',
            'yes no | ./install.sh'
        ]
