import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedtools",
    version="0.0.1",
    author="VisLab, Jeremy Cockfield, Alexander Jones, Owen Winterberg, Ian Callanan, Kay Robbins",
    author_email="Kay.Robbins@utsa.edu",
    description="Utilities for converting among different representations of the HED " +
                "(Hierarchical Event Descriptor) specification.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/hedtools/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
