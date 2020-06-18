import setuptools

with open("../hedconversion/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedconversion",
    version="0.0.3",
    author="VisLab, Jeremy Cockfield, Ian Callanan, Kay Robbins",
    author_email="Kay.Robbins@utsa.edu",
    description="Utilities for converting between wikimedia and XML representations of the HED schema.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/hedconversion/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

