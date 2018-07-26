from setuptools import find_packages, setup

test_requirements = open('test-requirements.txt').read().splitlines()

with open('requirements.txt') as requirements:
    setup(
        name='supervisor-elastic',
        version='0.0.1',
        description='Stream supervisord logs to elastic via redis',
        author='Wouter van Bommel',
        author_email='wouter@vanbommelonline.nl',
        url='https://github.com/woutervb/supervisor-elastic',
        license='GPLv2',
        long_description=open('README.md').read(),
        packages=find_packages(exclude=['tests']),
        package_data={
            'supervisor-elastic': [
                'README.md',
                'requirements.txt',
                'test-requirements.txt',
            ],
        },
        entry_points={
            'console_scripts': [
                'supervisor_elastic = supervisor_elastic:main',
            ],
        },
        install_requires=requirements.read().splitlines(),
        tests_require=test_requirements,
        test_suite='tests',
        extras_require={
            'tests': test_requirements,
        },
    )
