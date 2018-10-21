# -*- coding: utf-8 -*-
import textwrap
import functools


class Composer(object):

    def __init__(self, modules, cuda_ver, cudnn_ver, versions={}):
        if len(modules) == 0:
            raise ValueError('Modules should contain at least one module')
        pending = self._traverse(modules)
        self.modules = [m for m in self._toposort(pending)]
        self.instances = self._get_instances(versions)
        self.cuda_ver = cuda_ver
        self.cudnn_ver = cudnn_ver

    def get(self):
        return self.modules

    def ver(self, module):
        for ins in self.instances:
            if ins.__class__ is module:
                return ins.version
        return None

    def to_dockerfile(self, ubuntu_ver='16.04', join_mode='module'):
        if join_mode not in ['module', 'all']:
            try:
                join_mode = bool(join_mode)
            except ValueError:
                raise ValueError('join_mode must be None, \'module\' or \'all\'')

        if self.cuda_ver:
            base_image = 'nvidia/cuda:%s-cudnn%s-devel-ubuntu%s' % (
                self.cuda_ver, self.cudnn_ver, ubuntu_ver)
        else:
            base_image = 'ubuntu:%s' % ubuntu_ver

        module_list = self._split(
            ['module list',
             '\n'.join([repr(m) for m in self.instances if repr(m)])
             ])

        parts = [
            module_list,
            ('FROM', base_image),
            ('RUN', r'APT_INSTALL="apt-get install -y --no-install-recommends"'),
            ('RUN', r'PIP_INSTALL="python -m pip --no-cache-dir install --upgrade"'),
            ('RUN', r'GIT_CLONE="git clone --depth 10"'),
            '',
            ('RUN', r'''
                    rm -rf /var/lib/apt/lists/* \
                        /etc/apt/sources.list.d/cuda.list \
                        /etc/apt/sources.list.d/nvidia-ml.list
                    '''),
            '',
            ('RUN', 'apt-get update')
        ]

        # process module statements
        for m in self.instances:
            parts.append(self._split([m.name()]))
            for run_stmt in m.build():
                parts.append(('RUN', textwrap.dedent(run_stmt.rstrip())))

        ports = ' '.join([str(p) for m in self.instances for p in m.expose()])
        parts += [self._split(['config & cleanup']),
                  ('RUN', 'ldconfig'),
                  ('RUN', 'apt-get clean'),
                  ('RUN', 'apt-get autoremove'),
                  ('RUN', 'rm -rf /var/lib/apt/lists/* /tmp/* ~/*'),
                  '',
                  ('EXPOSE', ports if ports else '')]

        return self._join_parts(parts, join_mode)

    def _join_parts(self, parts, join_mode):
        last_run_idx = max([i for i, part in enumerate(parts)
                            if isinstance(part, tuple) and part[0] == 'RUN'])
        last_cmd = None
        paragraphs = []
        block = []
        join_next_run = False
        for i, part in enumerate(parts):
            if isinstance(part, tuple):
                cmd, text_raw = part
                text = self._indent(1, textwrap.dedent(text_raw.strip('\n').rstrip()))
                text_raw = text_raw.strip()
                if cmd == 'RUN' and join_next_run and i != last_run_idx:
                    text += ' && \\'
                if cmd == 'RUN' and join_next_run and last_cmd == 'RUN' and text_raw:
                    block.append(text)
                else:
                    if text_raw:
                        block.append('%s %s' % (cmd, text.strip()))
                    else:
                        block.append('')
                last_cmd = cmd
                if cmd == 'RUN' and join_mode in ['module', 'all']:
                    join_next_run = True
            else:
                if block:
                    paragraphs.append('\n'.join(['%s' % el for el in block]))
                    block = []
                if part.strip():
                    paragraphs.append(part.strip())
                join_next_run = join_mode == 'all'
        if block:
            paragraphs.append('\n'.join(block))

        return textwrap.dedent('\n\n'.join(paragraphs))

    def _indent(self, n, s):
        prefix = ' ' * 4 * n
        return ''.join(prefix + l for l in s.splitlines(True))

    def _traverse(self, modules):
        seen = set(modules)
        current_level = modules
        while current_level:
            next_level = []
            for module in current_level:
                yield module
                for child in (dep for dep in module.deps if dep not in seen):
                    next_level.append(child)
                    seen.add(child)
            current_level = next_level

    def _toposort(self, pending):
        data = {m: set(m.deps) for m in pending}
        for k, v in data.items():
            v.discard(k)
        extra_items_in_deps = functools.reduce(
            set.union, data.values()) - set(data.keys())
        data.update({item: set() for item in extra_items_in_deps})
        while True:
            ordered = set(item for item, dep in data.items() if len(dep) == 0)
            if not ordered:
                break
            for m in sorted(ordered, key=lambda m: m.__name__):
                yield m
            data = {
                item: (dep - ordered)
                for item, dep in data.items()
                if item not in ordered
            }
        if len(data) != 0:
            raise ValueError(
                'Circular dependencies exist among these items: '
                '{{{}}}'.format(', '.join(
                    '{!r}:{!r}'.format(
                        key, value) for key, value in sorted(
                        data.items()))))

    def _split(self, paragraphs=None):
        split_l = '# ' + '=' * 66 + '\n'
        split_s = '# ' + '-' * 66 + '\n'
        if paragraphs:
            formatted = []
            for p in paragraphs:
                formatted.append(''.join(['# %s\n' % line for line in p.splitlines()]))
            return ''.join([split_l,
                            split_s.join(formatted),
                            split_l])
        return split_l

    def _get_instances(self, versions):
        inses = []
        for m in self.modules:
            ins = m(self)
            if m in versions:
                ins.version = versions[m]
            inses.append(ins)
        return inses
