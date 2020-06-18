import setuptools

with open("../hedemail/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hedemail",
    version="0.0.1",
    author="VisLab, Jeremy Cockfield, Ian Callanan, Kay Robbins",
    author_email="Kay.Robbins@utsa.edu",
    description="Implementation of webhook to send email when wikimedia representation of the HED schema on GitHub changes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hed-standard/hed-python/hedemail/",
    packages=setuptools.find_namespace_packages(include=["hed.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

