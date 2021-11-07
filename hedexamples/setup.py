import setuptools

with open("../hedexamples/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedexamples",
    version="1.0.0",
    author="VisLab, Ian Callanan, Kay Robbins",
    author_email="Kay.Robbins@utsa.edu",
    description="Examples using the HED tools.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/master/hedexamples/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
