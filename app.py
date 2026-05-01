from flask import Flask, render_template, request, redirect
from backend.data_loader import load_all_data, update_behavior
from backend.recommender import RecommenderSystem
import pandas as pd
import random

random.seed(42)

app = Flask(__name__)

# تحميل البيانات الأساسية من ملفات الإكسل
users, products, ratings, behavior = load_all_data("data")

# إنشاء نظام التوصية
rec_system = RecommenderSystem(products, behavior, ratings, users)

# أعلام الدول (قد تظهر اختصارات بدل الأعلام حسب المتصفح/النظام)
FLAGS = {
    "Saudi Arabia": "🇸🇦",
    "Qatar": "🇶🇦",
    "UAE": "🇦🇪",
    "Kuwait": "🇰🇼",
    "Egypt": "🇪🇬",
    "Jordan": "🇯🇴",
    "Morocco": "🇲🇦",
}

# رموز الفئات (Emoji لكل نوع منتج)
CATEGORY_EMOJIS = {
    "Toys": "🧸",
    "Clothes": "👕",
    "Perfumes": "💐",
    "Sports": "🏅",
    "Home Appliances": "🏠",
    "Books": "📚",
    "Electronics": "💻",
}

@app.route("/")
def home():
    # صفحة البداية: عرض قائمة المستخدمين للاختيار
    user_ids = users["user_id"].tolist()
    return render_template("index.html", users=user_ids)

@app.route("/recommend", methods=["GET", "POST"])
def recommend():
    # الحصول على user_id من الفورم أو الرابط
    if request.method == "POST":
        user_id = int(request.form["user_id"])
    else:
        user_id = int(request.args.get("user_id"))

    # الحصول على أفضل توصيات للمستخدم
    product_ids = rec_system.get_recommendations(user_id)[:5]

    # تحديث ملف السلوك (زيادة عدد المشاهدات)
    global behavior
    behavior = pd.read_excel("data/behavior.xlsx")
    for pid in product_ids:
        behavior = update_behavior(behavior, user_id, pid, "view")
    behavior.to_excel("data/behavior.xlsx", index=False)

    # تجهيز بيانات التوصيات مع التقييمات والسلوك
    recommendations = products[products["product_id"].isin(product_ids)].copy()
    ratings_df = pd.read_excel("data/ratings.xlsx")
    all_ratings = ratings_df.groupby("product_id")["rating"].agg(["mean", "count"]).reset_index()
    all_ratings.rename(columns={"mean": "avg_rating", "count": "rating_count"}, inplace=True)
    recommendations = recommendations.merge(all_ratings, on="product_id", how="left")
    recommendations["avg_rating"] = recommendations["avg_rating"].fillna(0).apply(lambda x: round(float(x), 2))
    recommendations["rating_count"] = recommendations["rating_count"].fillna(0).astype(int)

    behavior_clean = behavior.groupby("product_id").sum().reset_index()
    recommendations = recommendations.merge(behavior_clean, on="product_id", how="left")

    # إضافة الرموز التعبيرية للفئات
    recommendations["emoji"] = recommendations["category"].apply(lambda c: CATEGORY_EMOJIS.get(c, ""))

    # بيانات المستخدم (العمر + البلد + العلم)
    user_row = users[users["user_id"] == user_id].iloc[0]
    user_age = int(user_row["age"])
    user_country = str(user_row["country"])
    user_flag = FLAGS.get(user_country, "")

    return render_template(
        "results.html",
        user_id=user_id,
        user_age=user_age,
        user_country=user_country,
        user_flag=user_flag,
        recommendations=recommendations.to_dict(orient="records")
    )

@app.route("/click/<int:product_id>/<int:user_id>")
def click(product_id, user_id):
    # تحديث السلوك عند النقر على منتج
    global behavior
    behavior = pd.read_excel("data/behavior.xlsx")
    behavior = update_behavior(behavior, user_id, product_id, "click")
    behavior.to_excel("data/behavior.xlsx", index=False)
    return "", 204

@app.route("/rate", methods=["POST"])
def rate():
    # صفحة تقييم المنتج
    user_id = int(request.form["user_id"])
    product_id = int(request.form["product_id"])

    global behavior
    behavior = pd.read_excel("data/behavior.xlsx")
    behavior = update_behavior(behavior, user_id, product_id, "click")
    behavior.to_excel("data/behavior.xlsx", index=False)

    return render_template("rate.html",
                           user_id=user_id,
                           product_id=product_id)
@app.route("/save_rating", methods=["POST"])
def save_rating():
    # حفظ التقييم الجديد أو تحديث التقييم القديم
    user_id = int(request.form["user_id"])
    product_id = int(request.form["product_id"])
    rating = int(request.form["rating"])

    ratings = pd.read_excel("data/ratings.xlsx")
    mask = (ratings["user_id"] == user_id) & (ratings["product_id"] == product_id)

    if ratings[mask].empty:
        ratings.loc[len(ratings)] = [user_id, product_id, rating]
    else:
        ratings.loc[mask, "rating"] = rating

    ratings.to_excel("data/ratings.xlsx", index=False)
    return redirect("/")

@app.route("/buy", methods=["POST"])
def buy():
    # تحديث السلوك عند شراء منتج
    user_id = int(request.form["user_id"])
    product_id = int(request.form["product_id"])

    global behavior
    behavior = pd.read_excel("data/behavior.xlsx")
    behavior = update_behavior(behavior, user_id, product_id, "purchase")
    behavior.to_excel("data/behavior.xlsx", index=False)

    return redirect(f"/recommend?user_id={user_id}")

if __name__ == "__main__":
    # تشغيل التطبيق
    app.run(debug=False, use_reloader=False)
