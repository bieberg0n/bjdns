import codecs
from setuptools import setup, find_packages


with codecs.open('Readme.md', encoding='utf-8') as f:
	long_description = f.read()

setup(
	name="bjdns",
	version="161019",
	description="A dns server that can protect yourself against DNS poisoning in China",
	author='bjdns',
	url='https://github.com/bieberg0n/bjdns',
	packages=find_packages(),
	packages_dir = {'':'bjdns'},
	package_data={
		'bjdns': ['Readme.md', 'LICENSE'],
		'': ['*.txt'],
	},
	install_requires=['gevent>=1.1'],
	entry_points="""
	[console_scripts]
	bjdns = bjdns.bjdns:main
	""",
	classifiers=[
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
	],
	long_description=long_description,
)
