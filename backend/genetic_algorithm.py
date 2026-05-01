import random

random.seed(42)

class GeneticRecommender:
    # هذا الكلاس يطبق خوارزمية الجينات لتوليد توصيات المنتجات للمستخدمين
    def __init__(self, products, behavior, ratings, users, user_id,
                 population_size=20, chromosome_length=5, generations=30):

        # تخزين البيانات الأساسية
        self.products = products
        self.behavior = behavior
        self.ratings = ratings
        self.users = users
        self.user_id = user_id

        # إعدادات الخوارزمية
        self.population_size = population_size
        self.chromosome_length = chromosome_length
        self.generations = generations

        # حساب السلوك العام لكل منتج
        self.behavior_dict = (
            self.behavior.groupby("product_id")[["viewed", "clicked", "purchased"]]
            .sum()
            .to_dict("index")
        )

        # حساب مجموع وعدد التقييمات لكل منتج
        self.rating_sum = (
            self.ratings.groupby("product_id")["rating"]
            .sum()
            .to_dict()
        )
        self.rating_count = (
            self.ratings.groupby("product_id")["rating"]
            .count()
            .to_dict()
        )

        # بيانات المستخدم الفردية
        self.user_behavior = self.behavior[self.behavior["user_id"] == self.user_id]
        self.user_ratings = self.ratings[self.ratings["user_id"] == self.user_id]

        # المنتجات التي شاهدها أو ضغط عليها أو قيّمها المستخدم
        self.user_viewed = set(self.user_behavior[self.user_behavior["viewed"] > 0]["product_id"])
        self.user_clicked = set(self.user_behavior[self.user_behavior["clicked"] > 0]["product_id"])
        self.user_rated = set(self.user_ratings["product_id"])

        # بيانات العمر والبلد للمستخدم
        user_row = self.users[self.users["user_id"] == self.user_id].iloc[0]
        self.user_age = int(user_row["age"])
        self.user_country = str(user_row["country"])

        # قائمة كل المنتجات
        self.product_ids = self.products["product_id"].tolist()

        # كاش لحفظ نتائج اللياقة
        self.fitness_cache = {}

        # تفضيلات حسب البلد
        self.country_preferences = {
            "Qatar": ["Perfumes", "Electronics", "Clothes"],
            "UAE": ["Perfumes", "Electronics", "Home Appliances"],
            "Saudi Arabia": ["Perfumes", "Electronics", "Sports"],
            "Kuwait": ["Clothes", "Perfumes", "Electronics"],
            "Egypt": ["Books", "Home Appliances", "Clothes"],
            "Jordan": ["Books", "Electronics", "Clothes"],
            "Morocco": ["Books", "Home Appliances", "Clothes"]
        }

    def fix_duplicates(self, chromosome):
        # إزالة التكرار من الكروموسوم وإضافة عناصر جديدة إذا لزم
        unique = list(dict.fromkeys(chromosome))
        while len(unique) < self.chromosome_length:
            new_item = random.choice(self.product_ids)
            if new_item not in unique:
                unique.append(new_item)
        return unique

    def generate_chromosome(self):
        # توليد كروموسوم عشوائي من المنتجات
        return random.sample(self.product_ids, self.chromosome_length)

    def generate_population(self):
        # توليد مجموعة أولية من الكروموسومات
        return [self.generate_chromosome() for _ in range(self.population_size)]

    def fitness(self, chromosome):
        # حساب درجة اللياقة لكل كروموسوم بناءً على السلوك والتقييمات والعمر والبلد
        key = tuple(chromosome)
        if key in self.fitness_cache:
            return self.fitness_cache[key]

        score = 0
        for product in chromosome:
            b = self.behavior_dict.get(product, {"viewed": 0, "clicked": 0, "purchased": 0})
            r_sum = self.rating_sum.get(product, 0)
            r_count = self.rating_count.get(product, 0)

            # تأثير السلوك العام
            score += b.get("viewed", 0) * 1
            score += b.get("clicked", 0) * 2
            score += b.get("purchased", 0) * 3
            score += r_sum * 2
            if r_count > 0:
                score -= 1
                # تأثير سلوك المستخدم الفردي
            if product in self.user_viewed:
                score += 200
            if product in self.user_clicked:
                score += 400
            if product in self.user_rated:
                score += 600

            # تأثير العمر
            product_category = self.products[self.products["product_id"] == product]["category"].iloc[0]
            if self.user_age < 30 and product_category in ["Sports", "Toys"]:
                score += 200
            elif 30 <= self.user_age <= 50 and product_category in ["Electronics", "Clothes"]:
                score += 200
            elif self.user_age > 50 and product_category in ["Books", "Home Appliances", "Perfumes"]:
                score += 200

            # تأثير البلد
            preferred = self.country_preferences.get(self.user_country, [])
            if product_category in preferred:
                score += 250

        self.fitness_cache[key] = score
        return score

    def selection(self, population):
        # اختيار أفضل كروموسومين من السكان الحاليين
        scored = [(chrom, self.fitness(chrom)) for chrom in population]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:2]

    def crossover(self, parent1, parent2):
        # دمج جزئي بين كروموسومين
        point = random.randint(1, self.chromosome_length - 1)
        return parent1[:point] + parent2[point:]

    def mutate(self, chromosome):
        # تعديل عشوائي بسيط على الكروموسوم
        if random.random() < 0.1:
            idx = random.randint(0, self.chromosome_length - 1)
            chromosome[idx] = random.choice(self.product_ids)
        return chromosome

    def run(self):
        # تشغيل الخوارزمية عبر عدة أجيال للحصول على أفضل توصيات
        random.seed(42)
        population = self.generate_population()
        for _ in range(self.generations):
            parents = self.selection(population)
            parent1, parent2 = parents[0][0], parents[1][0]
            new_population = []
            for _ in range(self.population_size):
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                child = self.fix_duplicates(child)
                new_population.append(child)
            population = new_population
        best = self.selection(population)[0][0]
        return best
