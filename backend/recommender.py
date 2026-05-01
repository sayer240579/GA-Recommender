from backend.genetic_algorithm import GeneticRecommender
from backend.data_loader import load_all_data

class RecommenderSystem:
    # هذا الكلاس مسؤول عن تشغيل نظام التوصية وتجهيز البيانات اللازمة للخوارزمية
    def __init__(self, products, behavior, ratings, users):
        # تخزين البيانات الأساسية داخل الكائن لاستخدامها لاحقًا
        self.products = products
        self.behavior = behavior
        self.ratings = ratings
        self.users = users

    def get_recommendations(self, user_id):
        # إعادة تحميل البيانات من ملفات الإكسل لضمان أن النظام يعمل على أحدث نسخة
        users, products, ratings, behavior = load_all_data("data")

        # إنشاء خوارزمية الجينات وتمرير بيانات المستخدم لها لتوليد التوصيات
        ga = GeneticRecommender(
            products=products,
            behavior=behavior,
            ratings=ratings,
            users=users,
            user_id=user_id,
            population_size=20,      # عدد الكروموسومات داخل كل جيل
            chromosome_length=5,     # عدد المنتجات المقترحة داخل كل كروموسوم
            generations=30           # عدد الأجيال التي تتطور خلالها الخوارزمية
        )

        # تشغيل الخوارزمية للحصول على أفضل مجموعة توصيات
        best = ga.run()
        return best
