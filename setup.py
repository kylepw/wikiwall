from setuptools import setup


with open('README.rst', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='wikiwall',
    version='0.0.4',
    author='Kyle Weeks',
    author_email='kylepw@gmail.com',
    description='Set desktop background to random Wikiart image.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT License',
    url='https://github.com/kylepw/wikiwall',
    py_modules=['wikiwall'],
    install_requires=[
        'Click',
        'BeautifulSoup4',
        'lxml',
        'requests',
        'tqdm'
    ],
    test_suite='tests',
    classifiers=[
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
    ],
    entry_points='''
        [console_scripts]
        wikiwall=wikiwall:cli
    '''
)
