import pandas as pd
import os

def load_all_data(data_path):
    users = pd.read_excel(os.path.join(data_path, "users.xlsx"))
    products = pd.read_excel(os.path.join(data_path, "products.xlsx"))
    ratings = pd.read_excel(os.path.join(data_path, "ratings.xlsx"))
    behavior = pd.read_excel(os.path.join(data_path, "behavior.xlsx"))
    return users, products, ratings, behavior

def update_behavior(behavior_df, user_id, product_id, action):
    mask = (behavior_df["user_id"] == user_id) & (behavior_df["product_id"] == product_id)

    if mask.any():
        idx = behavior_df[mask].index[0]

        if action == "view":
            behavior_df.at[idx, "viewed"] += 1
        elif action == "click":
            behavior_df.at[idx, "clicked"] += 1
        elif action == "purchase":
            behavior_df.at[idx, "purchased"] += 1

    else:
        behavior_df.loc[len(behavior_df)] = [
            user_id,
            product_id,
            1 if action == "view" else 0,
            1 if action == "click" else 0,
            1 if action == "purchase" else 0
        ]

    return behavior_df