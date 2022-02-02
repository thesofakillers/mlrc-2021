import os, string

import gensim.models as gm
import pandas as pd
from tqdm import tqdm
import numpy as np
import random

from badseeds import utils, metrics, seedbank


def merge_on_list(left: pd.DataFrame, right: pd.DataFrame, by: list):
    """Joins two dataframes by some columns where the column values are lists.
    This is an outer left join.
    :param pd.DataFrame left: dataframe to join to
    :param pd.DataFrame right: dataframe to join from
    :param list by: list of columns to merge on (all contain lists)
    :returns pd.DataFrame joined: joined dataframe
    """
    print(f"Merging {right.shape} df into {left.shape} df by {by}")
    name = [i + "_key" for i in by]

    # convert list to string
    left[name] = left[by].applymap(str)
    right[name] = right[by].applymap(str)
    right = right.drop(columns=by)
    print(left)
    print(right)

    # joins and drops new key columns
    joined = left.merge(right, on=name, how="left")
    joined.drop(name, axis=1, inplace=True)

    print(f"results in {joined.shape} df")

    return joined


def agg_coherence(all_coh: pd.DataFrame):
    """
    Returns average and rounded coherence across models
    :param list all_coh: list of coherence dataframes for each model
    :returns pd.DataFrame coh_avg: dataframe of average coherence across models for seed pairs
    """

    # average coherence scores across models
    coh_con = pd.concat(all_coh)
    if "Set ID A" in coh_con.columns and "Set ID B" in coh_con.columns:
        coh_avg = coh_con.groupby(["Set ID A", "Set ID B"]).agg({"Coherence": ["mean"]})
    else:
        coh_avg = coh_con.groupby(["Set A", "Set B"]).agg({"Coherence": ["mean"]})

    coh_avg.columns = ["Coherence"]
    coh_avg = coh_avg.reset_index()

    if "Set ID A" not in coh_avg.columns and "Set ID B" not in coh_avg.columns:
        coh_avg[["Set A", "Set B"]] = coh_avg[["Set A", "Set B"]].applymap(
            lambda x: eval(x)
        )

    coh_avg = coh_avg.sort_values(by="Coherence", ascending=False)

    return coh_avg


def append_row(
    coh: float,
    results: dict,
    seeds: pd.DataFrame,
    i: int,
    j: int,
):
    """
    Appends a row of coherence metrics and seed sets to results dataframe
    :param float coh: coherence score
    :param dict results: dict of lists {'Coherence': [], 'Set A': [], 'Set B': []}
    :param pd.DataFrame seeds: Dataframe of seed sets. Needs 1 "Seeds" column.
    :param int i: index of seed set A
    :param int j: index of seed set B
    :returns None
    """
    # build row
    results["Coherence"].append(coh)

    if "Seeds ID" in seeds.columns:
        results["Set ID A"].append(seeds["Seeds ID"][i])
        results["Set ID B"].append(seeds["Seeds ID"][j])
    else:
        results["Set A"].append(str(seeds.Seeds[i]))
        results["Set B"].append(str(seeds.Seeds[j]))
    return


def clean_tab_4(coh_avg: pd.DataFrame, seeds: pd.DataFrame, prefix: str):
    """
    Cleans coherence dataframe for tab 4
    :param pd.DataFrame coh_avg: dataframe of average coherence across models for seed pairs
    :param pd.DataFrame seeds: Dataframe of seed sets.
    :param str prefix: prefix for seed sets, "generated" or "gathered"
    :returns pd.DataFrame coh_avg: cleaned dataframe
    """

    if "Set ID A" in coh_avg.columns and "Set ID B" in coh_avg.columns:
        coh_avg["Set A"] = coh_avg["Set ID A"].apply(
            lambda x: seeds.Category[x].upper() + ": " + str(seeds.Seeds[x])
        )
        coh_avg["Set B"] = coh_avg["Set ID B"].apply(
            lambda x: seeds.Category[x].upper() + ": " + str(seeds.Seeds[x])
        )
        coh_avg.drop(columns=["Set ID A", "Set ID B"], inplace=True)
    else:
        coh_avg = coh_avg[["Coherence", "Set A", "Set B"]]
        coh_avg[["Set A", "Set B"]] = coh_avg[["Set A", "Set B"]].applymap(str)

    coh_avg.Coherence = coh_avg.Coherence.round(3)
    coh_avg.columns = ["Coherence", prefix + " Set A", prefix + " Set B"]
    coh_avg.replace(r"\[|\]|'", "", regex=True, inplace=True)

    return coh_avg


def build_row_table4(
    model: gm.KeyedVectors,
    seeds: pd.DataFrame,
    pairing_method: str = "window",
    pair_path: str = None,
    coh_mode: str = "weat",
) -> pd.DataFrame:
    """
    Builds a dataframe of coherence metrics
    for every possible pair of seed sets given embeddings
    :param gm.KeyedVectors model: embeddings model
    :param pd.Dataframe seeds: Dataframe of seed sets. Needs at least 1 "Seeds" column.
    :param str pairing_method: pairing method to use.
        'window' for moving window, 'all' for all possible pairs
        'file' when loading pairing data, requires pair_path
    :param str pair_path: path to pairing data, if pairing_method is 'file'. Default is None
    :param str coh_mode: coherence mode to use. "weat" for WEAT, "pca" for PCA. Default is "weat".
    :returns pd.DataFrame results: dataframe of coher. metrics for every poss. pair of seed sets
    """
    if pairing_method == "file":
        if pair_path:
            pairs = pd.read_csv(pair_path)
        else:
            print("Need a path to pairing data if pairing_method is 'file'")

    results = {
        "Coherence": [],
        "Set A": [],
        "Set B": [],
        "Set ID A": [],
        "Set ID B": [],
    }
    if pairing_method != "file":
        for i in range(seeds.shape[0]):
            if pairing_method == "window":
                lim = min(i + 2, seeds.shape[0])
            else:
                lim = seeds.shape[0]
            for j in range(i + 1, lim):
                if len(seeds.Seeds[i]) > 0 and len(seeds.Seeds[j]) > 0:
                    try:
                        # to avoid overlapping seeds
                        if set(seeds.Seeds[i]) & set(seeds.Seeds[j]):
                            continue
                        coh = metrics.coherence(
                            model, seeds.Seeds[i], seeds.Seeds[j], mode=coh_mode
                        )
                    except KeyError:
                        # print("One of seeds not found in model.")
                        continue
                    append_row(coh, results, seeds, i, j)
    else:
        for k in range(pairs.shape[0]):
            # find pair index
            seeds.set_index("Seeds ID", inplace=True, drop=False, verify_integrity=True)
            i = pairs[pairs.columns[0]][k]
            j = pairs[pairs.columns[1]][k]

            # do coherence
            if len(seeds.Seeds[i]) > 0 and len(seeds.Seeds[j]) > 0:
                try:
                    coh = metrics.coherence(
                        model, seeds.Seeds[i], seeds.Seeds[j], mode=coh_mode
                    )
                except KeyError:
                    continue

                append_row(coh, results, seeds, i, j)

    # normalize
    results = {k: v for k, v in results.items() if v}
    results["Coherence"] /= np.max(results["Coherence"])

    # make into df
    results = pd.DataFrame(results)
    return results


# if __name__ == "__main__":
#     import argparse

#     # get root dir and set it as working directory
#     fdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     os.chdir(fdir)

#     # Command line arguments
#     parser = argparse.ArgumentParser()
#     parser.add_argument(
#         "--embeddings_dir",
#         "-d",
#         default="models/nytimes_news_articles_min10",
#         type=str,
#         help="Path to directory of embeddings."
#         " If relative path, relative to root directory."
#         " Default is NYT dataset embeddings.",
#     )
#     parser.add_argument(
#         "--mode",
#         "-m",
#         default="gathered",
#         type=str,
#         help="Generated or gathered seeds.",
#     )
#     parser.add_argument(
#         "--coh",
#         "-c",
#         default="weat",
#         type=str,
#         help="Coherence mode. WEAT or PCA.",
#     )
#     args = parser.parse_args()

#     # load embeddings
#     models = []
#     for file in os.listdir(args.embeddings_dir):
#         if file.endswith(".kv"):
#             models.append(gm.KeyedVectors.load(os.path.join(args.embeddings_dir, file)))

#     if len(models) == 0:
#         raise ValueError("No embeddings found in directory.")

#     if args.mode == "gathered":
#         # part 1: gathered seeds
#         # load in all gathered seeds to memory, clean up
#         seeds = seedbank.seedbanking("data/seeds/seeds.json")
#         prefix = "Gathered"

#         # get coherence numbers
#         all_coherence = []
#         for model in tqdm(models, unit="model"):
#             coh = build_row_table4(
#                 model,
#                 seeds,
#                 pairing_method="file",
#                 pair_path="./seed_set_pairings.csv",
#                 coh_mode=args.coh,
#             )
#             all_coherence.append(coh)

#         # aggregate
#         coh_avg = agg_coherence(all_coherence)

#         # clean up for display
#         coh_avg = clean_tab_4(coh_avg, seeds, prefix)

#         coh_avg.to_csv("data/table4_gathered.csv", index=False)

#         # display
#         with pd.option_context("display.max_rows", 9, "display.max_colwidth", 60):
#             print(coh_avg)

#     elif args.mode == "generated":
#         check = string.printable
#         np.random.seed(42)
#         random.seed(42)
#         # generate random seeds, ignore non-alpha characters
#         sampled = []
#         for model in random.choices(models, k=50):
#             while True:
#                 s = utils.generate_seed_set(model)
#                 if 0 not in [c in check for w in s for c in w]:
#                     sampled.append(s)
#                     break

#         g_seeds = pd.DataFrame(data=pd.Series(sampled), columns=["Seeds"])

#         # check for duplicates in seeds
#         if 0 in g_seeds.apply(str).duplicated():
#             raise ValueError("Duplicate seeds found.")

#         prefix = "Generated"

#         # do coherence
#         all_coherence = []
#         for model in tqdm(models, unit="model"):
#             coh = build_row_table4(
#                 model, g_seeds, pairing_method="all", coh_mode=args.coh
#             )
#             all_coherence.append(coh)

#         # aggregate
#         coh_avg = agg_coherence(all_coherence)

#         coh_avg = clean_tab_4(coh_avg, g_seeds, prefix)

#         coh_avg.to_csv("data/table4_generated.csv", index=False)

#         # display
#         with pd.option_context("display.max_rows", 9, "display.max_colwidth", 100):
#             print(coh_avg)

#     else:
#         df = pd.read_csv("data/table4_generated.csv")
#         df.columns = ["Coherence", "Set A", "Set B"]
#         df[["Set A", "Set B"]] = df[["Set A", "Set B"]].applymap(
#             lambda x: x.split(", ")
#         )

#         # generate random seeds, ignore non-alpha characters
#         check = string.printable
#         np.random.seed(42)
#         random.seed(42)
#         sampled = []
#         for model in random.choices(models, k=50):
#             while True:
#                 s = utils.generate_seed_set(model)
#                 if 0 not in [c in check for w in s for c in w]:
#                     sampled.append(s)
#                     break

#         g_seeds = pd.DataFrame(data=pd.Series(sampled), columns=["Seeds"])
#         paired = []
#         for i in range(g_seeds.shape[0]):
#             for j in range(i + 1, g_seeds.shape[0]):
#                 paired.append([g_seeds.Seeds[i], g_seeds.Seeds[j]])
#         paired = pd.DataFrame(data=paired, columns=["Set A", "Set B"])

#         # merge
#         print(merge_on_list(df, paired, ["Set A", "Set B"]))
