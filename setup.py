from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="nanomock",
      version="0.0.21",
      author="gr0vity",
      description="Create local dockerized nano-currency networks",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/gr0vity-dev/nanomock",
      packages=find_packages(exclude=["unit_tests"]),
      include_package_data=True,
      install_requires=[
          "pyyaml",
          "tomli_w",
          "tomli",
          "oyaml",
          "nano_lib_py",
          "extradict",
          "nanorpc",
          'bitmath',
      ],
      entry_points={
          'console_scripts': [
              'nanomock=nanomock.main:main',
          ],
      })
