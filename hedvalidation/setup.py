import setuptools

with open("../hedvalidation/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedvalidation",
    version="1.0.0",
    author="VisLab, Jeremy Cockfield, Alexander Jones, Owen Winterberg, Ian Callanan, Kay Robbins",
    author_email="Kay.Robbins@utsa.edu",
    description="Python tools used to validate strings and spreadsheets containing tags against a HED (Hierarchical Event Descriptor) schema.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/hedvalidation/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
