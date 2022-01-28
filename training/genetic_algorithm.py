import logging
import numpy as np
from play import evaluate_player
from constants import NUM_ACTIONS, GENOME_LENGTH, POPULATION_SIZE, OFFSPRING_SIZE, TOURNAMEN_SIZE, \
    MUTATION_PROBABILITY, EVALUATION_IT, NUM_GENERATIONS, ELITISM_SIZE


def parent_selection(population, pop_fitness):
    tournament = np.random.randint(0, len(population), size=(TOURNAMEN_SIZE,))
    if pop_fitness is None:
        fitness = np.array([evaluate_player(EVALUATION_IT, list(population[t])) for t in tournament])
    else:
        np.sort(pop_fitness)
        fitness = np.array([pop_fitness[t] for t in tournament])
    return np.copy(population[tournament[fitness.argmin()]])


def xover(parent1, parent2): 
    offspring = np.zeros(parent1.shape) - 1
    xover_type = np.random.choice([0,1,2]) # randomly select which crossover type to execute
    #xover_type = np.random.choice([0]) # randomly select which crossover type to execute

    if xover_type == 0: # cycle crossover
        i = np.random.randint(0, GENOME_LENGTH - 1)
        j = np.random.randint(0, GENOME_LENGTH)
        while j <= i:
            j = np.random.randint(0, GENOME_LENGTH)
        offspring[i:j] = parent2[i:j]
        for n in parent1:
            if n not in offspring:
                c = np.where(offspring == -1)[0][0]
                offspring[c] = n

    elif xover_type == 1: # partially mapped crossover
        i = np.random.randint(0, GENOME_LENGTH - 1)
        j = np.random.randint(0, GENOME_LENGTH)
        while j <= i:
            j = np.random.randint(0, GENOME_LENGTH)
        offspring[i:j] = parent1[i:j]
        for c in range(i,j):
            t = np.where(parent2 == parent1[c])[0][0]
            if parent2[c] not in offspring and (t < i or t >= j):
                offspring[t] = parent2[c]
        for n in parent2:
            if n not in offspring:
                offspring[np.where(offspring == -1)[0][0]] = n

    elif xover_type == 2: # inver over
        offspring = parent1.copy()
        i = np.random.randint(0, GENOME_LENGTH)
        c = np.where(parent2 == parent1[i])[0][0]
        j = np.where(parent1 == parent2[(c+1) % GENOME_LENGTH])[0][0]
        while j <= i:
            i = np.random.randint(0, GENOME_LENGTH)
            c = np.where(parent2 == parent1[i])[0][0]
            j = np.where(parent1 == parent2[(c+1) % GENOME_LENGTH])[0][0]
        
        offspring[(i+1) % GENOME_LENGTH] = parent2[(c+1) % GENOME_LENGTH]
        offspring[i+2:j+1] = parent1[j-1:i:-1]
            
    return offspring


def mutate(parent):
    offspring = np.copy(parent)
    new_parent = None
    while np.random.random() < MUTATION_PROBABILITY: # keep mutating with some probability
        if new_parent is None:
            new_parent = parent
        else:
            new_parent = offspring.copy()
        mutation = np.random.choice([0,0,1,2,3]) 
        #mutation = np.random.choice([0]) 
        # randomly choose which type of mutation to perform (more likely
        # to perform easier mutation)

        if mutation == 0: #swap mutation
            i = np.random.randint(0, GENOME_LENGTH)
            j = np.random.randint(0, GENOME_LENGTH)
            while j == i:
                j = np.random.randint(0, GENOME_LENGTH)
            offspring[i], offspring[j] = new_parent[j], new_parent[i]

        elif mutation == 1: #inversion mutation
            i = np.random.randint(1, GENOME_LENGTH-1)
            j = np.random.randint(0, GENOME_LENGTH)
            while j <= i:
                j = np.random.randint(0, GENOME_LENGTH)
            offspring[i:j] = new_parent[j-1:i-1:-1]

        elif mutation == 2: #scramble mutation
            i = np.random.randint(1, GENOME_LENGTH-1)
            j = np.random.randint(0, GENOME_LENGTH)
            while j <= i:
                j = np.random.randint(0, GENOME_LENGTH)
            np.random.shuffle(offspring[i:j])   

        elif mutation == 3: #insert mutation
            i = np.random.randint(1, GENOME_LENGTH-1)
            j = np.random.randint(0, GENOME_LENGTH)
            while j <= i:
                j = np.random.randint(0, GENOME_LENGTH)
            offspring[i+1] = new_parent[j]
            offspring[i+2:j+1] = new_parent[i+1:j]
    return offspring


def main():

    # initial random solution
    solution = np.array(range(NUM_ACTIONS))
    np.random.shuffle(solution)
    best_fitness = evaluate_player(EVALUATION_IT, list(solution))

    # initial population
    population = np.array(np.zeros((POPULATION_SIZE, GENOME_LENGTH)))
    population[0, :] = solution
    for i in range(1, POPULATION_SIZE):
        population[i, :] = np.array(range(NUM_ACTIONS))
        np.random.shuffle(population[i,:])

    fitness = np.array([evaluate_player(EVALUATION_IT, list(o)) for o in population])
    generations = 1
    count_gen_with_no_improvements = 0
    best_fitness_overall = 0
    best_individual_so_far = []
    history = []
    #while count_gen_with_no_improvements < NO_IMPROVEMENT: # continue until a steady state is reached
    while generations < NUM_GENERATIONS:
        print(f"**** Generation {generations} ****")
        generations += 1
        offspring = list()
        print("--- Generate offspring")
        for i in range(ELITISM_SIZE):
            offspring.append(population[i].copy()) # Copy best ELITISM_SIZE individuals to next generation
        for _ in range(OFFSPRING_SIZE - ELITISM_SIZE):
            p1, p2 = parent_selection(population, fitness), parent_selection(population, fitness)
            offspring.append(mutate(xover(p1, p2)))
        offspring = np.array(offspring)
        print("--- Evaluate offspring")
        fitness = np.array([evaluate_player(EVALUATION_IT, list(o)) for o in offspring])
        print("--- Perform survival selection")
        population = np.copy(offspring[fitness.argsort()[:]][:POPULATION_SIZE])
        best_fitness = fitness.min()
        if best_fitness < best_fitness_overall:
            best_fitness_overall = best_fitness
            best_individual_so_far = list(population[0])
            count_gen_with_no_improvements = 0
        else:
            count_gen_with_no_improvements += 1
        history.append(best_fitness)
        print(f"--- Best fitness: {best_fitness} --- Best individual: {list(population[0])}")

    print(f"Problem solved in {generations} generations")
    print(f"Best individual is ", end='')
    print(best_individual_so_far, end='')
    print(f" with fitness {best_fitness_overall}")
    
    #np.save("population", population)
    #np.save("fitness", fitness)
    #np.save("history", np.array(history))

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    logging.getLogger().setLevel(level=logging.INFO)
    main()