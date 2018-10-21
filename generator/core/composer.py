# -*- coding: utf-8 -*-
import textwrap
import functools
from itertools import chain, product
from operator import itemgetter


class Composer(object):

    def __init__(self, modules, cuda_ver, cudnn_ver):
        if len(modules) == 0:
            raise ValueError('Modules should contain at least one module')
        pending = list(self._traverse(modules))
        self.modules = [m for m in self._toposort(pending)]
        self.cuda_ver = cuda_ver
        self.cudnn_ver = cudnn_ver

    def get(self):
        return self.modules

    def ver(self, module):
        for ins in self.modules:
            if ins.__class__ is module:
                return ins.version
        return None

    def get_base_module(self, ubuntu_ver):
        if self.cuda_ver:
            base_image = 'nvidia/cuda:%s-cudnn%s-devel-ubuntu%s' % (
                self.cuda_ver, self.cudnn_ver, ubuntu_ver)
        else:
            base_image = 'ubuntu:%s' % ubuntu_ver

        parts = [
            ('FROM', base_image),
            ('ENV', r'APT_INSTALL apt-get install -y --no-install-recommends'),
            ('ENV', r'PIP_INSTALL python -m pip --no-cache-dir install --upgrade'),
            ('ENV', r'GIT_CLONE git clone --depth 10'),
            '',
            ('RUN', r'''
                    rm -rf /var/lib/apt/lists/* \
                        /etc/apt/sources.list.d/cuda.list \
                        /etc/apt/sources.list.d/nvidia-ml.list
                    '''),
            '',
            ('RUN', 'apt-get update')
        ]

        return (
            ['module list',
             '\n'.join([repr(m) for m in self.modules if repr(m)])],
            parts
        )

    def to_dockerfile(self, ubuntu_ver='16.04', join_mode='module'):
        ports = ' '.join([str(p) for m in self.modules for p in m.expose()])

        module_tuples = [self.get_base_module(ubuntu_ver)]
        for m in self.modules:
            parts = []
            for run_stmt in m.build(self):
                parts.append(('RUN', textwrap.dedent(run_stmt.rstrip())))
            module_tuples.append(([m.name()], parts))
        module_tuples.append((
            ['config & cleanup'],
            [
              ('RUN', 'ldconfig'),
              ('RUN', 'apt-get clean'),
              ('RUN', 'apt-get autoremove'),
              ('RUN', 'rm -rf /var/lib/apt/lists/* /tmp/* ~/*'),
              '',
              ('EXPOSE', ports if ports else '')
            ]
        ))

        return self._join_module_tuples(module_tuples, join_mode)

    def _join_module_tuples(self, module_tuples, join_mode='module'):
        if join_mode not in ['module', 'all']:
            try:
                join_mode = bool(int(join_mode))
                if join_mode:
                    raise ValueError
            except ValueError:
                raise ValueError('join_mode must be None, \'module\' or \'all\'')

        def get_last_run_id(_stmts):
            runs = list([part for part in _stmts
                         if isinstance(part, tuple) and part[0] == 'RUN'])
            if not runs:
                return None
            return id(runs[-1])

        module_stmts = list(chain.from_iterable(map(itemgetter(1), module_tuples)))
        last_run = get_last_run_id(module_stmts)
        last_cmd = None
        parts = []
        for header, stmts in module_tuples:
            parts.append(self._split(header))

            last_run_of_module = get_last_run_id(stmts)
            first_run = True
            block = []
            for stmt in stmts:
                if isinstance(stmt, tuple):
                    cmd, text_raw = stmt
                    text = textwrap.dedent(text_raw.strip('\n').rstrip())
                    text_raw = text_raw.strip()

                    if ((join_mode == 'all' and text is not last_run) or
                       (join_mode == 'module' and id(stmt) != last_run_of_module)) and \
                            last_cmd == 'RUN' and cmd == 'RUN' and text_raw:
                        text += ' && \\'

                    if (last_cmd != 'RUN' or not join_mode or (join_mode == 'module' and first_run) or cmd != last_cmd) and text_raw:
                        block.append('%s %s' % (cmd, textwrap.indent(text.strip(), ' ' * 4).lstrip()))
                        first_run = False
                    else:
                        block.append(textwrap.indent(text,  ' ' * 4))

                    last_cmd = cmd
                else:
                    if block:
                        parts.append('\n'.join(block))
                        block = []
                    if stmt.strip():
                        parts.append(stmt.strip())

            if block:
                parts.append('\n'.join(block))

        parts = map(lambda s: s.strip('\n'), parts)
        return '\n\n'.join(parts)

    def _traverse(self, modules):
        seen = set(m.__class__ for m in modules)
        current_level = modules
        while current_level:
            next_level = []
            for module in current_level:
                yield module
                unseen_deps = list(dep for dep in module.deps if dep not in seen)
                for dep_module in unseen_deps:
                    ins = dep_module()
                    next_level.append(ins)
                    seen.add(dep_module)
            current_level = next_level

    def _toposort(self, pending):
        data = {}
        for m in pending:
            deps = {ins for ins, dep in product(pending, m.deps)
                    if ins.__class__ == dep}
            data[m] = deps
        for k, v in data.items():
            v.discard(k)
        extra_items_in_deps = functools.reduce(
            set.union, data.values()) - set(data.keys())
        data.update({item: set() for item in extra_items_in_deps})
        while True:
            ordered = set(item for item, dep in data.items() if len(dep) == 0)
            if not ordered:
                break
            for m in sorted(ordered, key=lambda m: m.name()):
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
