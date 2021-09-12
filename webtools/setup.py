import setuptools

with open("../hedweb/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedweb",
    version="1.0.0",
    author="VisLab, Jeremy Cockfield, Ian Callanan, Kay Robbins",
    author_email="Kay.Robbins@utsa.edu",
    description="Web interface for HED tools.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/hedweb/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
