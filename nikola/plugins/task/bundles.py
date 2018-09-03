# -*- coding: utf-8 -*-

# Copyright © 2012-2018 Roberto Alsina and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Bundle assets."""


import configparser
import io
import itertools
import os
import shutil

from nikola.plugin_categories import LateTask
from nikola import utils


class BuildBundles(LateTask):
    """Bundle assets."""

    name = "create_bundles"

    def gen_tasks(self):
        """Bundle assets."""
        kw = {
            'filters': self.site.config['FILTERS'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'cache_folder': self.site.config['CACHE_FOLDER'],
            'theme_bundles': get_theme_bundles(self.site.THEMES),
            'themes': self.site.THEMES,
            'files_folders': self.site.config['FILES_FOLDERS'],
            'code_color_scheme': self.site.config['CODE_COLOR_SCHEME'],
        }

        def build_bundle(output, inputs):
            out_dir = os.path.join(kw['output_folder'],
                                   os.path.dirname(output))
            inputs = [
                os.path.join(
                    out_dir,
                    os.path.relpath(i, out_dir))
                for i in inputs if os.path.isfile(i)
            ]
            with open(os.path.join(out_dir, os.path.basename(output)), 'wb+') as out_fh:
                for i in inputs:
                    with open(i, 'rb') as in_fh:
                        shutil.copyfileobj(in_fh, out_fh)
                    out_fh.write(b'\n')

        yield self.group_task()

        if self.site.config['USE_BUNDLES']:
            for name, _files in kw['theme_bundles'].items():
                output_path = os.path.join(kw['output_folder'], name)
                dname = os.path.dirname(name)
                files = []
                for fname in _files:
                    # paths are relative to dirname
                    files.append(os.path.join(dname, fname))
                file_dep = [os.path.join(kw['output_folder'], fname)
                            for fname in files if
                            utils.get_asset_path(
                                fname,
                                self.site.THEMES,
                                self.site.config['FILES_FOLDERS'],
                                output_dir=kw['output_folder']) or fname == os.path.join('assets', 'css', 'code.css')]
                # code.css will be generated by us if it does not exist in
                # FILES_FOLDERS or theme assets.  It is guaranteed that the
                # generation will happen before this task.
                task = {
                    'file_dep': list(file_dep),
                    'task_dep': ['copy_assets', 'copy_files'],
                    'basename': str(self.name),
                    'name': str(output_path),
                    'actions': [(build_bundle, (name, file_dep))],
                    'targets': [output_path],
                    'uptodate': [
                        utils.config_changed({
                            1: kw,
                            2: file_dep
                        }, 'nikola.plugins.task.bundles')],
                    'clean': True,
                }
                yield utils.apply_filters(task, kw['filters'])


def get_theme_bundles(themes):
    """Given a theme chain, return the bundle definitions."""
    for theme_name in themes:
        bundles_path = os.path.join(
            utils.get_theme_path(theme_name), 'bundles')
        if os.path.isfile(bundles_path):
            config = configparser.ConfigParser()
            header = io.StringIO('[bundles]\n')
            with open(bundles_path, 'rt') as fd:
                config.read_file(itertools.chain(header, fd))
            bundles = {}
            for name, files in config['bundles'].items():
                name = name.strip().replace('/', os.sep)
                files = [f.strip() for f in files.split(',') if f.strip()]
                bundles[name] = files
            return bundles
