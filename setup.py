from distutils.core import setup
setup(
  name='task_template',
  py_modules=['task_template'],
  version='1.0.0',
  license='MIT',
  description='Template for cognitive tasks',
  author='ICRIN Lab',
  author_email='contact@icrin.fr',
  url='https://github.com/ICRIN-lab/task_template',
  download_url='https://github.com/ICRIN-lab/tak_template/archive/v1.0.0.tar.gz',
  keywords=['cognitive_task', 'neurosciences', 'experiment'],
  install_requires=[
          'psychopy',
          'wxPython',
      ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Neuroscientists',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
  ],
)
