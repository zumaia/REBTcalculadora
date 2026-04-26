from setuptools import setup, find_packages

setup(
    name="rebt-calculadora",
    version="1.0.0",
    description="Calculadora de instalaciones eléctricas según REBT",
    author="REBT Calculator",
    author_email="info@rebt-calculator.es",
    url="https://github.com/usuario/rebt-calculadora",
    packages=find_packages(),
    install_requires=[
        "flask>=3.0.0",
        "gunicorn>=21.0.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "rebt-calc=app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)