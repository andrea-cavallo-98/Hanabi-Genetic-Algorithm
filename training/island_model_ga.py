import copy
import multiprocessing
import os
import shutil

import numpy as np
from play import evaluate_player
import genetic_algorithm as ga
from constants import ELITISM_SIZE, NUM_ACTIONS, GENOME_LENGTH, POPULATION_SIZE, OFFSPRING_SIZE, EVALUATION_TYPE, \
    MUTATION_PROBABILITY, EVALUATION_IT, NUM_GENERATIONS, NUM_ISLANDS, MIGRATION_INTERVAL, MIGRATION_SIZE, LOAD_CHECKPOINT, \
        STARTING_SPLIT

class Population:
    def __init__(self, population_size, individual_size, mutation_rate, fitness_function, id, checkpoint_dir):
        self.population_size = population_size
        self.individual_size = individual_size
        self.mutation_rate = mutation_rate
        self.fitness_function = fitness_function
        self.id = id
        self.checkpoint_dir = checkpoint_dir

        assert population_size > 0
        assert individual_size > 0

        if LOAD_CHECKPOINT:
            self.individuals = np.load(self.checkpoint_dir + "ckp" + str(self.id) + ".npy")
        else:
            self.individuals = np.array(np.zeros((self.population_size, self.individual_size)))
            for i in range(self.population_size):
                self.individuals[i, :] = np.array(range(self.individual_size))
                np.random.shuffle(self.individuals[i,:])

        self.fitness = np.array([evaluate_player(EVALUATION_IT, list(o), EVALUATION_TYPE) for o in self.individuals])


    def get_best(self):
        return self.individuals[self.fitness.argmin()], self.fitness.min()

    def parent_selection(self):
        return ga.parent_selection(self.individuals, self.fitness)

    def select(self, k):
        weights = -self.fitness[:self.population_size]
        weights = weights - weights.min() + 1
        weights = weights / weights.sum()

        parents_indices = np.random.choice(range(self.population_size), size=k, p=weights)
        parents = self.individuals[parents_indices]
        return parents

    def crossover(self, parent1, parent2):
        return ga.xover(parent1, parent2)

    def mutate(self, parent):
        return ga.mutate(parent)

    def sort(self):
        self.individuals = np.copy(self.individuals[self.fitness.argsort()[:]][:self.population_size])

    def run(self, it, f):

        #if (self.individuals.shape != (self.population_size, self.individual_size)):
        #    print(f"### Something's wrong! ### Expected shape: {self.population_size},{self.individual_size} - Real shape: {self.individuals.shape}")

        self.fitness = np.array([evaluate_player(EVALUATION_IT, list(o), EVALUATION_TYPE) for o in self.individuals])
        self.individuals = np.copy(self.individuals[self.fitness.argsort()[:]][:self.population_size])
        self.fitness.sort()

        offspring = list()
        for i in range(ELITISM_SIZE):
            offspring.append(self.individuals[i].copy()) # Copy best ELITISM_SIZE individuals to next generation
        for _ in range(OFFSPRING_SIZE - ELITISM_SIZE):
            p1, p2 = self.parent_selection(), self.parent_selection()
            offspring.append(self.mutate(self.crossover(p1, p2)))
        offspring = np.array(offspring)
        self.fitness = np.array([evaluate_player(EVALUATION_IT, list(o), EVALUATION_TYPE) for o in offspring])
        self.individuals = np.copy(offspring[self.fitness.argsort()[:]][:self.population_size])
        self.fitness.sort()

        if (it + 1) % 5 == 0:
            np.save(self.checkpoint_dir + "ckp" + str(self.id), self.individuals)

        f.write(f"{self.id}, {it}, {self.fitness.min()}, {list(self.individuals[0])}\n")
        print(f"--- Island {self.id} --- It {it} --- Fitness: {self.fitness.min()} --- Best: {list(self.individuals[0])}")


class World:
    def __init__(self,
                 world_size,
                 population_size,
                 individual_size,
                 mutation_rate,
                 migration_interval,
                 migration_size,
                 fitness_function):
        self.world_size = world_size
        self.population_size = population_size
        self.individual_size = individual_size
        self.mutation_rate = mutation_rate
        self.migration_interval = migration_interval
        self.migration_size = migration_size
        self.fitness_function = fitness_function

        assert world_size > 0
        assert population_size > 0
        assert individual_size > 0

        self.results_dir = "./results/"
        self.checkpoint_dir = "./checkpoint/"
        self.log_files = ["log_" + str(i) + ".csv" for i in range(self.population_size)]
        self.islands = [Population(population_size, individual_size, mutation_rate, fitness_function, id, self.checkpoint_dir) for id in range(world_size)]

    def migrate(self):
        migrant_groups = []

        for island in self.islands:
            migrant_groups.append({
                "individuals": island.select(self.migration_size),
                "destination": np.random.randint(self.world_size)
            })

        for migrant_group in migrant_groups:
            for individual in migrant_group["individuals"]:
                migrant = copy.deepcopy(individual)
                self.islands[migrant_group["destination"]].individuals = \
                    np.concatenate((self.islands[migrant_group["destination"]].individuals, migrant.reshape(1,NUM_ACTIONS)))
                
    def run_parallel_island(self, island):
        with open(self.results_dir + "log_" + str(island.id) + ".csv", "a") as f:
            for i in range(self.migration_interval):
                island.run(i, f)
        return island

    def run_parallel(self, generations):
        assert self.world_size > 1
        assert self.migration_interval > 0
        assert self.migration_size > 0

        if not LOAD_CHECKPOINT: # otherwise, folders already exist
            ## Create results directory to store output results
            if os.path.exists(self.results_dir):
                shutil.rmtree(self.results_dir)
            os.makedirs(self.results_dir)

        if not LOAD_CHECKPOINT: # otherwise, folders already exist
            ## Create results directory to store checkpoints
            if os.path.exists(self.checkpoint_dir):
                shutil.rmtree(self.checkpoint_dir)
            os.makedirs(self.checkpoint_dir)
        
        with open(self.results_dir + "log_main.txt", "a") as f:

            splits = generations // self.migration_interval
            best_individual = None
            best_score = 0

            if LOAD_CHECKPOINT:
                best_score = -17.16
                best_individual = [1.0, 15.0, 12.0, 22.0, 24.0, 25.0, 21.0, 10.0, 8.0, 7.0, 9.0, 27.0, 5.0, 23.0, 26.0, 20.0, 17.0, 18.0, 14.0, 19.0, 28.0, 3.0, 0.0, 2.0, 6.0, 11.0, 4.0, 13.0, 16.0]
                for island in self.islands:
                    if island.get_best()[1] < best_score:
                        best_individual, best_score = island.get_best()

                f.write(f"generation {(STARTING_SPLIT - 1) * self.migration_interval}, score {best_score}, best individual {best_individual}\n")
                print(f"generation {(STARTING_SPLIT - 1) * self.migration_interval}, score {best_score}, best individual {best_individual}")
                self.migrate()


            for split in range(STARTING_SPLIT, splits):
                with multiprocessing.Pool() as pool:
                    self.islands = pool.map(self.run_parallel_island, self.islands)

                for island in self.islands:
                    if island.get_best()[1] < best_score:
                        best_individual, best_score = island.get_best()

                f.write(f"generation {split * self.migration_interval}, score {best_score}, best individual {list(best_individual)}\n")
                print(f"generation {split * self.migration_interval}, score {best_score}, best individual {list(best_individual)}")

                self.migrate()

            print("Generations limit reached.")


if __name__ == "__main__":
    
    world = World(
        world_size=NUM_ISLANDS,
        population_size=POPULATION_SIZE,
        individual_size=GENOME_LENGTH,
        mutation_rate=MUTATION_PROBABILITY,
        migration_interval=MIGRATION_INTERVAL,
        migration_size=MIGRATION_SIZE,
        fitness_function=evaluate_player
    )
    world.run_parallel(NUM_GENERATIONS)