
import io
import os

import setuptools


# Package metadata.

name = "Sendbox-{App}"
description = "The Sendbox {{App}} Project"
# Should be one of:
# 'Development Status :: 3 - Alpha'
# 'Development Status :: 4 - Beta'
# 'Development Status :: 5 - Production/Stable'
release_status = "Development Status :: 5 - Production/Stable"
dependencies = []
extras = {}


# Setup boilerplate below this line.

package_root = os.path.abspath(os.path.dirname(__file__))

version = {}
with open(os.path.join(package_root, "App/__init__.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]

# readme_filename = os.path.join(package_root, "README.rst")
# with io.open(readme_filename, encoding="utf-8") as readme_file:
#     readme = readme_file.read()
#
# # Only include packages under the 'google' namespace. Do not include tests,
# # benchmarks, etc.
# packages = [
#     package for package in setuptools.find_packages() if package.startswith("google")
# ]

# Determine which namespaces are needed.
# namespaces = ["google"]
# if "google.cloud" in packages:
#     namespaces.append("google.cloud")


setuptools.setup(
    name=name,
    version=version,
    description=description,
    # long_description=readme,
    author="Sendbox",
    author_email="admin@sendbox.ng",
    license="Apache 2.0",
    url="https://github.com/sendbox-software-inc/{{App}}",
    platforms="Posix; MacOS X; Windows",
    # packages=packages,
    # namespace_packages=namespaces,
    install_requires=dependencies,
    extras_require=extras,
    python_requires=">=3.6",
    include_package_data=True,
    zip_safe=False,
)