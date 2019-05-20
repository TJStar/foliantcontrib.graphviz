'''
GraphViz diagrams preprocessor for Foliant documenation authoring tool.
'''

import re

from pathlib import Path, PosixPath
from hashlib import md5
from subprocess import run, PIPE, STDOUT, CalledProcessError

from foliant.preprocessors.utils.combined_options import (Options,
                                                          CombinedOptions,
                                                          validate_in,
                                                          yaml_to_dict_convertor,
                                                          boolean_convertor)
from foliant.preprocessors.utils.preprocessor_ext import (BasePreprocessorExt,
                                                          allow_fail)

OptionValue = int or float or bool or str


class Preprocessor(BasePreprocessorExt):
    defaults = {
        'cache_dir': Path('.diagramscache'),
        'as_image': True,
        'graphviz_path': 'dot',
        'engine': 'dot',
        'format': 'png',
        'params': {},
        'fix_svg_size': True,
    }
    tags = ('graphviz',)
    supported_engines = ('circo', 'dot', 'fdp', 'neato', 'osage',
                         'patchwork', 'sfdp' 'twopi')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = Options(self.options,
                              defaults=self.defaults,
                              validators={'engine': validate_in(self.supported_engines)})

        self._cache_path = self.project_path / self.config['cache_dir']

        self.logger = self.logger.getChild('graphviz')

        self.logger.debug(f'Preprocessor inited: {self.__dict__}')

    def _get_command(self,
                     options: CombinedOptions,
                     diagram_src_path: PosixPath,
                     diagram_path: PosixPath) -> str:
        '''Generate the image generation command.

        :param options: a CombinedOptions object with tag and config options
        :param diagram_src_path: Path to the diagram source file
        :param diagram_src_path: Path to the diagram output file

        :returns: Complete image generation command
        '''

        components = [options['graphviz_path']]

        components.append(f'-T{options["format"]}')
        components.append(f'-K{options["engine"]}')
        components.append(f'-o {diagram_path}')

        for param_name, param_value in options['params'].items():
            if param_value is True:
                components.append(f'-{param_name}')
            else:
                components.append(f'-{param_name}={param_value}')

        components.append(str(diagram_src_path))

        return ' '.join(components)

    def _get_result(self, diagram_path: PosixPath, config: CombinedOptions):
        '''Get either image ref or raw image code depending on as_image option'''
        if config['as_image']:
            return f'![{config.get("caption", "")}]({diagram_path.absolute().as_posix()})'
        else:
            with open(diagram_path, 'r') as f:
                return f.read()

    def _fix_svg_size(self, svg_path: PosixPath):
        '''insert 100% instead of hardcoded height and width attributes'''
        p_width = r'(<svg .*width=").+?(")'
        p_height = r'(<svg .*height=").+?(")'

        with open(svg_path, encoding='utf8') as f:
            content = f.read()

        result = re.sub(p_width, r'\g<1>100%\g<2>', content)
        result = re.sub(p_height, r'\g<1>100%\g<2>', result)

        with open(svg_path, 'w', encoding='utf8') as f:
            f.write(result)

    @allow_fail('Error while processing graphviz tag.')
    def _process_diagrams(self, block) -> str:
        '''
        Process graphviz tag.
        Save GraphViz diagram body to .gv file, generate an image from it,
        and return the image ref.

        If the image for this diagram has already been generated, the existing version
        is used.

        :returns: Image ref
        '''
        tag_options = Options(self.get_options(block.group('options')),
                              validators={'engine': validate_in(self.supported_engines)},
                              convertors={'params': yaml_to_dict_convertor,
                                          'as_image': boolean_convertor,
                                          'fix_svg_size': boolean_convertor})
        options = CombinedOptions({'config': self.options,
                                   'tag': tag_options},
                                  priority='tag')
        body = block.group('body')

        self.logger.debug(f'Processing GraphViz diagram, options: {options}, body: {body}')

        body_hash = md5(f'{body}'.encode())
        body_hash.update(str(options.options).encode())

        diagram_src_path = self._cache_path / 'graphviz' / f'{body_hash.hexdigest()}.gv'

        self.logger.debug(f'Diagram definition file path: {diagram_src_path}')

        diagram_path = diagram_src_path.with_suffix(f'.{options["format"]}')

        self.logger.debug(f'Diagram image path: {diagram_path}')

        if diagram_path.exists():
            self.logger.debug('Diagram image found in cache')

            return self._get_result(diagram_path, options)

        diagram_src_path.parent.mkdir(parents=True, exist_ok=True)

        with open(diagram_src_path, 'w', encoding='utf8') as diagram_src_file:
            diagram_src_file.write(body)

            self.logger.debug(f'Diagram definition written into the file')

        try:
            command = self._get_command(options, diagram_src_path, diagram_path)
            self.logger.debug(f'Constructed command: {command}')
            run(command, shell=True, check=True, stdout=PIPE, stderr=STDOUT)

            if options['format'] == 'svg' and options['fix_svg_size']:
                self._fix_svg_size(diagram_path)

            self.logger.debug(f'Diagram image saved')

        except CalledProcessError as e:
            self._warning('Processing of GraphViz diagram failed.',
                          context=self.get_tag_context(block),
                          error=e)
            return block.group(0)
        return self._get_result(diagram_path, options)

    def apply(self):
        self._process_tags_for_all_files(self._process_diagrams)
        self.logger.info('Preprocessor applied')
