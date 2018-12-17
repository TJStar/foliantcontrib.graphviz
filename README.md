# Graphviz Diagrams Preprocessor for Foliant

[Graphviz](http://plantuml.com/) is an open source graph visualization tool. This preprocessor converts Graphviz diagram definitions in the source and converts them into images on the fly during project build.

## Installation

```bash
$ pip install foliantcontrib.graphviz
```

## Config

To enable the preprocessor, add `graphviz` to `preprocessors` section in the project config:

```yaml
preprocessors:
    - graphviz
```

The preprocessor has a number of options:

```yaml
preprocessors:
    - graphviz:
        cache_dir: !path .diagramscache
        graphviz_path: dot
        engine: dot
        format: png
        params:
            ...
```

`cache_dir`
:   Path to the directory with the generated diagrams. It can be a path relative to the project root or a global one; you can use `~/` shortcut.

>   To save time during build, only new and modified diagrams are rendered. The generated images are cached and reused in future builds.

`graphviz_path`
:   Path to Graphviz launcher. By default, it is assumed that you have the `dot` command in your `PATH`, but if Graphviz uses another command to launch, or if the `dot` launcher is installed in a custom place, you can define it here.

`engine`
:   Layout engine used to process the diagram source. Available engines: (`circo`, `dot`, `fdp`, `neato`, `osage`, `patchwork`, `sfdp` `twopi`). Default: `dot`

`format`
:   Output format of the diagram image. Available formats: [tons of them](https://graphviz.gitlab.io/_pages/doc/info/output.html). Default: `png`

`params`
:   Params passed to the image generation command:

        preprocessors:
            - graphviz:
                params:
                    Gdpi: 100

>To see the full list of params, run the command that launches Graphviz, with `-?` command line option.


## Usage

To insert a diagram definition in your Markdown source, enclose it between `<<graphviz>...</graphviz>` tags:

```markdown
Here’s a diagram:

<<graphviz>
    a -> b
</graphviz>
```

You can set any parameters in the tag options. Tag options have priority over the config options so you can override some values for specific diagrams while having the default ones set up in the config.

Tags also have an exclusive `caption` option — the markdown caption of the diagram image.

```markdown
Diagram with a caption:

<<graphviz caption="Deployment diagram"
           params="Earrowsize: 0.5">
    a -> b
</graphviz>
```

>Note that command params listed in the `params` option are stated in YAML format. Remember that YAML is sensitive to indentation so for several params it is more suitable to use JSON-like mappings: `{key1: 1, key2: 'value2'}`.