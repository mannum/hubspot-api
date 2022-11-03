from distutils.core import setup

from setuptools import find_packages

setup(
    name="hubspot-api",
    version="1.1.1",
    description="Superscript Hubspot API",
    author="Superscript",
    author_email="paul.lucas@gosuperscript.com",
    install_requires=["requests", "python-dotenv==0.19.2", "hubspot-api-client==5.0.1"],
    packages=find_packages(include=["hs_api*"]),
)
