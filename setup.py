from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name="bitmex_trader_bot",
    version="0.0.1",
    description="Trade with bitmex bot",
    long_description=readme,
    author="no-coin-no-life",
    author_email="no.coin.no.life@gmail.com",
    url="https://github.com/no-coin-no-life/bitmex-trader-bot",
    license=license,
    packages=find_packages(exclude=("tests"))
)