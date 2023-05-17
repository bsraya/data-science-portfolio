import pandas as pd
import os

# get all csv files in the ./datasets folder
# Path: ./datasets
files = os.listdir("./datasets/dirty/store-sales-time/")

for file in files:
    # read csv file
    # Path: ./datasets/file
    df = pd.read_csv("./datasets/dirty/store-sales-time/" + file)

    # write the new csv file
    # Path: ./datasets/cleaned/file
    df.to_parquet(
        "./datasets/cleaned/store-sales-time/" + file.strip(".csv") + ".parquet"
    )
