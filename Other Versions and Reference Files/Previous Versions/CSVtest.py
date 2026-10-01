import pandas as pd


def open_csv(csv_file):
    x = pd.read_csv(csv_file)

    print(x.head())

    return x


open_csv("Greenhouse_Model_Global_Assumptions.csv")
