from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='S1_NRB',
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    description="Prototype processor for the Sentinel-1 Normalized Radar Backscatter (S1 NRB) product",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/SAR-ARD/S1_NRB",
    author="John Truckenbrodt, Marco Wolsza",
    author_email="marco.wolsza@uni-jena.de",
    packages=find_packages(where='.'),
    include_package_data=True,
    install_requires=['gdal>=3.4.1',
                      'click',
                      'lxml',
                      'pystac',
                      'pyroSAR @ git+https://github.com/johntruckenbrodt/pyroSAR.git',
                      'spatialist>=0.10.0',
                      'scipy'],
    python_requires='>=3.8',
    zip_safe=False,
    entry_points={
        'console_scripts': ['s1_nrb=S1_NRB.cli:cli']
    }
)
