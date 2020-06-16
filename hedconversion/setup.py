import setuptools

with open("../hedconversion/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedconversion",
    version="0.0.3",
    author="VisLab",
    author_email="author@example.com",
    description="Test version of hedconversion dist",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/hedconversion/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

