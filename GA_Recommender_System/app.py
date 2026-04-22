from flask import Flask, render_template, request, redirect
from backend.data_loader import load_all_data, update_behavior
from backend.recommender import RecommenderSystem
import pandas as pd

app = Flask(__name__)
users, products, ratings, behavior = load_all_data("data")
rec_system = RecommenderSystem(products, behavior, ratings)

@app.route("/")
def home():
    user_ids = users["user_id"].tolist()
    return render_template("index.html", users=user_ids)

@app.route("/recommend", methods=["GET", "POST"])
def recommend():

    if request.method == "POST":
        user_id = int(request.form["user_id"])
    else:
        user_id = int(request.args.get("user_id"))

    product_ids = rec_system.get_recommendations()[:5]

    global behavior
    for pid in product_ids:
        behavior = update_behavior(behavior, user_id, pid, "view")

    recommendations = products[products["product_id"].isin(product_ids)]

    ratings = pd.read_excel("data/ratings.xlsx")
    print("PRODUCTS IDs:", products["product_id"].unique()[:20])
    print("RATINGS IDs:", ratings["product_id"].unique()[:20])
    print("PRODUCTS TYPE:", products["product_id"].dtype)
    print("RATINGS TYPE:", ratings["product_id"].dtype)
    user_ratings = ratings[ratings["user_id"] == user_id]
    recommendations = recommendations.merge(user_ratings, on="product_id", how="left")
    ratings = pd.read_excel("data/ratings.xlsx")
    all_ratings = ratings.groupby("product_id")["rating"].agg(["mean", "count"]).reset_index()
    all_ratings.rename(columns={"mean": "avg_rating", "count": "rating_count"}, inplace=True)
    recommendations = recommendations.merge(all_ratings, on="product_id", how="left")

    recommendations["avg_rating"] = recommendations["avg_rating"].fillna(0).apply(lambda x: round(float(x), 2))
    recommendations["rating_count"] = recommendations["rating_count"].fillna(0).astype(int)

    behavior_clean = behavior.groupby("product_id").sum().reset_index()
    recommendations = recommendations.merge(behavior_clean, on="product_id", how="left")

    return render_template(
        "results.html",
        user_id=user_id,
        recommendations=recommendations.to_dict(orient="records")
    )

@app.route("/rate", methods=["POST"])
def rate():
    user_id = int(request.form["user_id"])
    product_id = int(request.form["product_id"])

    # تحميل ملف السلوك
    behavior = pd.read_excel("data/behavior.xlsx")

    # تحديث السلوك
    behavior = update_behavior(behavior, user_id, product_id, "click")

    # حفظ الملف
    behavior.to_excel("data/behavior.xlsx", index=False)

    return render_template("rate.html",
                           user_id=user_id,
                           product_id=product_id)

@app.route("/save_rating", methods=["POST"])
def save_rating():
    import pandas as pd

    user_id = int(request.form["user_id"])
    product_id = int(request.form["product_id"])
    rating = int(request.form["rating"])

    # تحميل ملف التقييمات
    ratings = pd.read_excel("data/ratings.xlsx")

    # إضافة تقييم جديد
    ratings.loc[len(ratings)] = [user_id, product_id, rating]

    # حفظ الملف
    ratings.to_excel("data/ratings.xlsx", index=False)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
