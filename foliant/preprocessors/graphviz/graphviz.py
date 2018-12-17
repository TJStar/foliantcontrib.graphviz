'''
GraphViz diagrams preprocessor for Foliant documenation authoring tool.
'''

from pathlib import Path, PosixPath
from shutil import copyfile
from hashlib import md5
from subprocess import run, PIPE, STDOUT, CalledProcessError
from foliant.preprocessors.base import BasePreprocessor

from .combined_options import (Options, CombinedOptions, validate_in,
                               yaml_to_dict_convertor)

OptionValue = int or float or bool or str


class Preprocessor(BasePreprocessor):
    defaults = {
        'cache_dir': Path('.diagramscache'),
        'graphviz_path': 'dot',
        'engine': 'dot',
        'format': 'png',
        'params': {}
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

    def process_diagrams(self, content: str) -> str:
        '''Find diagram definitions and replace them with image refs.

        The definitions are fed to GraphViz processor that converts them into images.

        :param content: Markdown content

        :returns: Markdown content with diagrams definitions replaced with image refs
        '''

        def _sub(block) -> str:
            '''Save GraphViz diagram body to .gv file, generate an image from it,
            and return the image ref.

            If the image for this diagram has already been generated, the existing version
            is used.

            :param options: Options extracted from the diagram definition
            :param body: GraphViz diagram body

            :returns: Image ref
            '''
            body = block.group('body')
            tag_options = Options(self.get_options(block.group('options')),
                                  validators={'engine': validate_in(self.supported_engines)},
                                  convertors={'params': yaml_to_dict_convertor})
            options = CombinedOptions({'config': self.options,
                                       'tag': tag_options},
                                      priority='tag')

            self.logger.debug(f'Processing GraphViz diagram, options: {options}, body: {body}')

            body_hash = md5(f'{body}'.encode())
            body_hash.update(str(options.options).encode())

            diagram_src_path = self._cache_path / 'graphviz' / f'{body_hash.hexdigest()}.gv'

            self.logger.debug(f'Diagram definition file path: {diagram_src_path}')

            diagram_path = diagram_src_path.with_suffix(f'.{options["format"]}')

            self.logger.debug(f'Diagram image path: {diagram_path}')

            img_ref = f'![{options.get("caption", "")}]({diagram_path.absolute().as_posix()})'

            if diagram_path.exists():
                self.logger.debug('Diagram image found in cache')

                return img_ref

            diagram_src_path.parent.mkdir(parents=True, exist_ok=True)

            if 'src' in options:
                copyfile(self.working_dir / options['src'], diagram_src_path)
                self.logger.debug(f'Diagram defined in external file. Copied into cache folder')
            else:
                with open(diagram_src_path, 'w', encoding='utf8') as diagram_src_file:
                    diagram_src_file.write(body)

                    self.logger.debug(f'Diagram definition written into the file')

            try:
                command = self._get_command(options, diagram_src_path, diagram_path)
                self.logger.debug(f'Constructed command: {command}')
                run(command, shell=True, check=True, stdout=PIPE, stderr=STDOUT)

                self.logger.debug(f'Diagram image saved')

            except CalledProcessError as exception:
                self.logger.error(str(exception))

                raise RuntimeError(
                    f'Processing of GraphViz diagram {diagram_src_path} failed: {exception.output.decode()}'
                )

            return img_ref

        return self.pattern.sub(_sub, content)

    def apply(self):
        self.logger.info('Applying preprocessor')

        for markdown_file_path in self.working_dir.rglob('*.md'):
            with open(markdown_file_path, encoding='utf8') as markdown_file:
                content = markdown_file.read()

            processed = self.process_diagrams(content)

            with open(markdown_file_path, 'w', encoding='utf8') as markdown_file:
                markdown_file.write(processed)

        self.logger.info('Preprocessor applied')
