from distutils.core import setup

setup(
    name="hupspot-api",
    version="0.1",
    description="Superscript Hubspot API",
    author="Superscript",
    author_email="paul.lucas@gosuperscript.com",
    install_requires=["requests", "python-dotenv==0.19.2", "hubspot-api-client==5.0.1"],
)
