from setuptools import setup


SHORT_DESCRIPTION = 'GraphViz diagrams preprocessor for Foliant.'

try:
    with open('README.md', encoding='utf8') as readme:
        LONG_DESCRIPTION = readme.read()

except FileNotFoundError:
    LONG_DESCRIPTION = SHORT_DESCRIPTION


setup(
    name='foliantcontrib.graphviz',
    description=SHORT_DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    version='1.0.1',
    author='Daniil Minukhin',
    author_email='ddddsa@gmail.com',
    url='https://github.com/foliant-docs/foliantcontrib.graphviz',
    packages=['foliant.preprocessors.graphviz'],
    license='MIT',
    platforms='any',
    install_requires=[
        'foliant>=1.0.4'
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Documentation",
        "Topic :: Utilities",
    ]
)
