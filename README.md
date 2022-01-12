# Bad Seeds: Evaluating Lexical Methods for Bias Measurement

This repository contains the code for reproducing the results presented in the
paper
[_Bad Seeds: Evaluating Lexical Methods for Bias Measurement_](https://aclanthology.org/2021.acl-long.148/)
as presented in our paper _Badder Seeds: Reproducing the Evaluation of Lexical
Methods for Bias Measurement_ as part of the
[2021 ML Reproducibility Challenge](https://paperswithcode.com/rc2021/)

## Usage

### Setup

For clearer specification of our setup, we make use of
[Poetry](https://python-poetry.org/) to keep track of dependencies and python
versions. Details such as python and package versions can be found in the
generated [pyproject.toml](pyproject.toml) and [poetry.lock](poetry.lock) files.

For poetry users, getting setup is as easy as running

```terminal
poetry install
```

We also provide an [environment.yml](environment.yml) file for
[Conda](https://docs.conda.io/projects/conda/en/latest/index.html) users who do
not wish to use poetry. In this case simply run

```terminal
conda env create -f environment.yml
```

Finally, if neither of the above options are desired, we also provide a
[requirements.txt](requirements.txt) file for
[pip](https://pypi.org/project/pip/) users. In this case, simply run

```terminal
pip install -r requirements.txt
```

### Repository Structure

```bash
.
├── badseeds # scripts
│   └── __init__.py
├── notebooks # notebooks for reproduction, which import scripts
│   └── results.ipynb
├── README.md # you are here
├── environment.yml # if you are using conda
├── poetry.lock # handled by poetry
├── pyproject.toml # if you are using poetry
└── requirements.txt # if you are using pip
```

Users interested in only reproducing the results should visit the
[notebooks/](notebooks/) subdirectory of the repository, where we have a set of
notebooks that can be run to reproduce the results of our paper.

For more curious users, we invite them to visit the [badseeds/](badseeds/)
subdirectory which contains the actual implementation details.

## Development

If you wish to contribute to this repository, please make use of
[Poetry](./https://python-poetry.org/) when installing new packages, as this
makes dependency management much easier and transparent.
