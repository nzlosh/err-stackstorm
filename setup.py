import setuptools

from lib.version import ERR_STACKSTORM_VERSION

setuptools.setup(
    name="err-stackstorm",
    version=ERR_STACKSTORM_VERSION,
    author="Err-StackStorm Plugin contributors",
    author_email="nzlosh@yahoo.com",
    description="An Errbot plugin for StackStorm ChatOps.",
    long_description="Not available",
    long_description_content_type="text/markdown",
    url="https://github.com/nzlosh/err-stackstorm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ],
)
