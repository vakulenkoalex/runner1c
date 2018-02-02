from setuptools import setup, find_packages
import runner1c

setup(
    name='runner1c',
    version=runner1c.__version__,
    url='https://github.com/vakulenkoalex/runner1c/',
    license='BSD',
    author='Vakulenko Aleksei',
    # author_email = 'vakulenko_alex',
    packages=find_packages(),
    description='example',
    include_package_data=True,
    platforms='win32',
    entry_points={
        'console_scripts': [
            'runner1c = runner1c.core:main',
        ],
    }
)
