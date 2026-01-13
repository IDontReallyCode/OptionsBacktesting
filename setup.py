import setuptools

setuptools.setup(
    name='optionbacktester',
    version='0.1.0',
    description='Event-driven backtester for Options and Equities',
    url='#',
    author='Pascal Letourneau',
    author_email='',
    
    # 1. Automatically find packages (currently finds "src")
    packages=setuptools.find_packages(),
    
    # 2. Dependencies (Pip will install these automatically)
    install_requires=[
        'polars>=0.20.0',   # The engine core
        'pyarrow>=14.0.0',  # Required for efficient file IO
        'pandas',           # Good to have for compatibility
        'pyyaml'            # If you use config.yaml
    ],
    
    # 3. Dev Dependencies (Optional, for running tests)
    extras_require={
        'dev': ['pytest', 'black', 'flake8'],
    },

    # 4. Enforce Python version (Polars likes newer python)
    python_requires='>=3.9',
    
    zip_safe=False
)