# YouTube-Commons (PleIAs / Hugging Face)
# %%
import pandas as pd
from datasets import load_dataset
from huggingface_hub import HfApi

# %%
api = HfApi()
files = api.list_repo_files("PleIAs/YouTube-Commons", repo_type="dataset")
parquet_files = [f for f in files if f.endswith(".parquet")]
print("total file:", len(parquet_files))

dfs = []
for f in parquet_files[:10]:
    path = f"hf://datasets/PleIAs/YouTube-Commons/{f}"
    df = pd.read_parquet(path, columns=["video_id", "original_language", "video_link"])
    print(f, len(df))
    dfs.append(df)

all_df = pd.concat(dfs, ignore_index=True)

# %%
df_en = all_df[all_df["original_language"] == "en"]
print(df_en)
# %%
import os

from parrot.collect_video_ids import DATASET_DIR

path = DATASET_DIR
df_en.to_csv(path, sep="\t", index=False)
print(os.path.getsize(path) / (1024 * 1024))


#### tublex
# %%
import glob

import pandas as pd

for p in glob.glob("/home/hoai/user/resource/tools/parrot/dataset/videos-en.csv"):
    df = pd.read_csv(p)
    print(p, df.shape)
    # print(df.columns.tolist())
    # print(df.head(100))
    # Select as a DataFrame, slice 10k rows, rename the column, and save
    df[["videoid"]][10000:].rename(columns={"videoid": "video_id"}).to_json(
        "/home/hoai/user/resource/tools/parrot/dataset/tubelex_vid.jsonl",
        orient="records",
        lines=True,
    )


# %%
import itertools
import time

from datasets import load_dataset

checked = {}  # video_id -> True/False
ds = load_dataset(
    "espnet/yodas", "en000", split="train", streaming=True, trust_remote_code=True
).remove_columns("audio")
for r in itertools.islice(ds, 10000):
    vid = r["utt_id"]
    print(vid)
