import random

random.seed(42)

class GeneticRecommender:
    def __init__(self, products, behavior, ratings,
        population_size=20, chromosome_length=5, generations=30):

        self.products = products
        self.behavior = behavior
        self.ratings = ratings
        self.population_size = population_size
        self.chromosome_length = chromosome_length
        self.generations = generations

        # Precomputed dictionaries (very fast)
        self.behavior_dict = (
            self.behavior.groupby("product_id")[["viewed", "clicked", "purchased"]]
            .sum()
            .to_dict("index")
        )

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

        self.product_ids = self.products["product_id"].tolist()

        self.fitness_cache = {}
    def fix_duplicates(self, chromosome):
        unique = list(dict.fromkeys(chromosome))

        while len(unique) < self.chromosome_length:
            new_item = random.choice(self.product_ids)
            if new_item not in unique:
                unique.append(new_item)

        return unique

    def generate_chromosome(self):
        return random.sample(self.product_ids, self.chromosome_length)

    def generate_population(self):
        return [self.generate_chromosome() for _ in range(self.population_size)]

    def fitness(self, chromosome):
        key = tuple(chromosome)
        if key in self.fitness_cache:
            return self.fitness_cache[key]

        score = 0

        for product in chromosome:
            b = self.behavior_dict.get(product, {"viewed": 0, "clicked": 0, "purchased": 0})
            r_sum = self.rating_sum.get(product, 0)
            r_count = self.rating_count.get(product, 0)

            score += b.get("viewed", 0) * 1
            score += b.get("clicked", 0) * 2
            score += b.get("purchased", 0) * 3

            score += r_sum * 2

            if r_count > 0:
                score -= 1

        self.fitness_cache[key] = score
        return score

    def selection(self, population):
        scored = [(chrom, self.fitness(chrom)) for chrom in population]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:2]

    def crossover(self, parent1, parent2):
        point = random.randint(1, self.chromosome_length - 1)
        return parent1[:point] + parent2[point:]

    def mutate(self, chromosome):
        if random.random() < 0.1:
            idx = random.randint(0, self.chromosome_length - 1)
            chromosome[idx] = random.choice(self.product_ids)
        return chromosome

    def run(self):
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