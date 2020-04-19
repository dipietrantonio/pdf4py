import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pdf4py",
    version="0.1.0",
    author="Cristian Di Pietrantonio",
    author_email="cristiandipietrantonio@gmail.com",
    description="A PDF parser written in Python3 with no external dependencies.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Halolegend94/pdf4py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
)