from setuptools import setup, find_packages
import configparser

config = configparser.ConfigParser()
config.read("setup.cfg")
metadata = config["metadata"]
options = config["options"]
# Define the setup() arguments
setup(
    name=metadata["name"],
    version='{{VERSION_PLACEHOLDER}}',
    author=metadata["author"],
    author_email=metadata["author_email"],
    description=metadata["description"],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url=metadata["url"],
    license=metadata["license"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["*.model"]},
    python_requires=">=3.6",
    install_requires=options["install_requires"],
    extras_require=config["options.extras_require"],
    classifiers=metadata["classifiers"].splitlines(),
)
