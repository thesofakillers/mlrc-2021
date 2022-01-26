"""
converts json seed file in sensible and structured format 
resources: https://raw.githubusercontent.com/maria-antoniak/bad-seeds/main/gathered_seeds.json

"""
import re
import pandas as pd
from sklearn import datasets


def clean(categories):
    """
    cleans seed .json file, sorts by category

    Parametrs
    -----------
    categories : pandas DatatFrame
        DataFrame with seeds and meta information

    Returns
    --------
    x: Pandas DatatFrame
        cleaned categories DataFrame with seeds and meta information

    """

    words = ["seed", "words", "terms", "attributes"]
    # print(''.join([i for i in categories if not i.isdigit()]))
    x = "".join([i for i in categories if not i.isdigit()])
    x = " ".join([w for w in x.split() if not w in words])
    x = x.replace("_", " ")
    x = x.replace("/", " ")

    return x


def get_seeds(seeds, seed_list):
    """
    returns seed by seed id

    Parametrs
    -----------
    seed_list : list of strings
        list of seed IDs

    Returns
    --------
    extracted_seeds: list of lists
        list of seeds

    """

    extracted_seeds = []

    for seed in seed_list:
        seed1 = seeds.loc[[seed], ["Seeds"]]
        extracted_seeds.append(pd.eval(seed1.values[0])[0])

    return extracted_seeds


def seedbanking(dataset):
    """
    loads .json as pandas DataFrame

    Parametrs
    -----------
    dataset : string
        seed.json directory

    Returns
    --------
    seeds: Pandas DataFrame
        ordered by category, DataFrame with seeds and meta information
    """
    seeds = pd.read_json(dataset)
    seeds["Category"] = seeds["Category"].apply(clean)
    seeds = seeds.sort_values(by="Category")

    return seeds


if __name__ == "__main__":
    seeds = seedbanking("../data/seeds/seeds.json")
    with pd.option_context(
        "display.max_rows",
        None,
        "display.precision",
        3,
    ):
        print(seeds)
