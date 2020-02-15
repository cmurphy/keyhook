import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="keystone-hook",
    version="0.0.1",
    author="Colleen Murphy",
    author_email="colleen.murphy@suse.com",
    description="Kubernetes webhook for keystone quotas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/keystone-hook",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
