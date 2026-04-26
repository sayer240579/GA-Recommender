from backend.genetic_algorithm import GeneticRecommender

class RecommenderSystem:
    def __init__(self, products, behavior, ratings):
        self.products = products
        self.behavior = behavior
        self.ratings = ratings

    def get_recommendations(self):
        ga = GeneticRecommender(
            products=self.products,
            behavior=self.behavior,
            ratings=self.ratings,
            population_size=20,
            chromosome_length=5,
            generations=30
        )

        best = ga.run()
        return best