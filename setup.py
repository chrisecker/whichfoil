# -*- coding: latin-1 -*-


from setuptools import setup, find_packages

with open('README') as file:
    long_description = file.read()

setup(name='whichfoil',
      version='0.0',
      description = 'A tool for identifying airfoils from bitmap images.',
      long_description = long_description,
      author = 'C. Ecker',
      author_email = 'textmodelview@gmail.com',
      #url = 'https://pypi.python.org/',
      license = 'BSD',
      packages = find_packages(exclude=['etc', 'test']),
      entry_points = {
          'console_scripts': [
              'whichfoil=whichfoil.main:main',
          ],
      },
      platforms = ['any'],

      package_data={
          "whichfoil": ["foils/*.dat"],
      }      
)

