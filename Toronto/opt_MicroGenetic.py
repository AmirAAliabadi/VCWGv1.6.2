# The micro genetic function
# Xuan Chen
# Atmospheric Innovations Research (AIR) Laboratory, University of Guelph, Guelph, Canada
# last update: 21 July 2022

import numpy
import random
import pandas


# Part 1: generate the population for each iteration
# Generate the first generation by random choosing among the variable space
def starting_pop(options_space, n_pop, n_var):
    # randomly choose n_pop times * number of variables
    pop = pandas.DataFrame(numpy.zeros((n_pop, n_var)), index=numpy.arange(n_pop), columns=options_space.keys())

    for i in range(n_pop):
        for ind in options_space:
            pop[ind].iloc[i] = random.sample(options_space[ind], 1)[0]
    return pop

# Generate the next generation if the condition meet the convergence in the inner loop
# The elite is an array
def out_pop(options_space, n_pop, n_var, n_change, elite):
    pop = pandas.DataFrame(numpy.zeros((n_pop, n_var)), index=numpy.arange(n_pop), columns=options_space.keys())

    for i in range(n_change):
        for ind in options_space:
            pop[ind].iloc[i] = random.sample(options_space[ind], 1)[0]
    pop.iloc[-1] = elite
    return pop

# Generate the next generation with the elite and the offsprings within the inner loop
# elite and offsprings are both arrays
def in_pop(options_space, n_pop, n_var, n_change, elite, offspring):
    pop = pandas.DataFrame(numpy.zeros((n_pop, n_var)), index=numpy.arange(n_pop), columns=options_space.keys())
    pop.iloc[0:n_change] = offspring
    pop.iloc[-1] = elite
    return pop

# Part 2 choosing the parents for next generation
# pop is a dataframe
# fitness is a dataframe
# Parents and elite are both arrays
def tournament(fitness, pop, n_change, n_var):
    # Sort the fitness values from small to big, smaller the better
    sort_fitness = fitness.sort_values(by=['FIT'])
    # Make sure even number to be paired parents (it takes two in a marriage)
    winners = sort_fitness.iloc[0:n_change, ]
    # After sorting, the index of the dataframe does not change, use the index to select the parents in population
    parents_idx = winners.index.values.tolist()
    parents = numpy.zeros((n_change, n_var))
    for i in range(n_change):
        address = parents_idx[i]
        parents[i, :] = numpy.array(pop.iloc[address])
    elite_idx = parents_idx[0]
    elite_fit = sort_fitness.iloc[0].values
    elite = parents[0, :]
    return parents, elite, elite_fit, elite_idx

# Part 3 crossover to get the offspring
# parents and offsprings are arrays
def crossover(parents, n_change, n_var):
    offspring = numpy.zeros((n_change, n_var))
    # The length of the DNA which contains each gene (variable)
    gene_len = n_var

    for i in range(int(n_change/2)):
        # The point at which crossover takes place between two parents
        # For example, if n_var = 3, cross over location is either 1 or 2
        crossover_point = random.randint(1, gene_len - 1)
        # Index of the first parent to mate
        parent1_idx = i
        # Index of the second parent to mate
        parent2_idx = i + int(n_change/2)
        # The new offspring will have its first half of its genes taken from the first parent
        offspring[i, 0:crossover_point] = parents[parent1_idx, 0:crossover_point]
        # The new offspring will have its second half of its genes taken from the second parent
        offspring[i, crossover_point:] = parents[parent2_idx, crossover_point:]

        offspring[i + int(n_change/2), 0:crossover_point] = parents[parent2_idx, 0:crossover_point]
        offspring[i + int(n_change/2), crossover_point:] = parents[parent1_idx, crossover_point:]

    return offspring