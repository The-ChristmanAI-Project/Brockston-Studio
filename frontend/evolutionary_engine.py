import math
import random
import json
import logging
import os
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class NeuralNetIndividual:
    """
    Represents an individual neural network architecture in the population.
    """
    def __init__(self, input_size: int, output_size: int, num_layers: int = 1, neurons_per_layer: int = 16):
        self.input_size = input_size
        self.output_size = output_size
        self.num_layers = min(num_layers, 4)
        self.neurons_per_layer = min(neurons_per_layer, 64)
        self.fitness = 0.0
        self.weights = self._initialize_weights()

    def _initialize_weights(self) -> List[List[List[float]]]:
        """
        Initialize simple CPU-friendly weight matrices.
        """
        weights = []
        # Input to first hidden layer
        layer_weights = [[random.uniform(-1, 1) for _ in range(self.input_size)] for _ in range(self.neurons_per_layer)]
        weights.append(layer_weights)
        
        # Hidden to hidden layers
        for _ in range(self.num_layers - 1):
            layer_weights = [[random.uniform(-1, 1) for _ in range(self.neurons_per_layer)] for _ in range(self.neurons_per_layer)]
            weights.append(layer_weights)
            
        # Last hidden to output layer
        layer_weights = [[random.uniform(-1, 1) for _ in range(self.neurons_per_layer)] for _ in range(self.output_size)]
        weights.append(layer_weights)
        
        return weights

    def build_model(self, input_size: int, output_size: int):
        """
        Dynamically configures the model to be reused by different systems.
        Supports varying input and output dimensions.
        """
        self.input_size = input_size
        self.output_size = output_size
        self.weights = self._initialize_weights()
        logger.info(f"Model rebuilt dynamically with Input: {input_size}, Output: {output_size}")

    def predict(self, inputs: List[float]) -> List[float]:
        """
        Forward pass using simple math to keep it CPU-friendly (Axiom 3).
        No external dependencies like numpy or torch.
        """
        if len(inputs) != self.input_size:
            # Pad or truncate if mismatch
            inputs = (inputs + [0.0] * self.input_size)[:self.input_size]
            
        activation = inputs
        for i, layer in enumerate(self.weights):
            next_activation = []
            for neuron_weights in layer:
                # Dot product
                val = sum(a * w for a, w in zip(activation, neuron_weights))
                # Simple leaky ReLU for hidden layers, Sigmoid for output
                if i < len(self.weights) - 1:
                    val = val if val > 0 else 0.01 * val
                else:
                    # Sigmoid for 0-1 range output
                    try:
                        val = 1.0 / (1.0 + math.exp(-max(min(val, 100), -100)))
                    except OverflowError:
                        val = 0.0 if val < 0 else 1.0
                next_activation.append(val)
            activation = next_activation
        return activation

    def to_dict(self) -> Dict[str, Any]:
        """Serialize individual for persistence."""
        return {
            "input_size": self.input_size,
            "output_size": self.output_size,
            "num_layers": self.num_layers,
            "neurons_per_layer": self.neurons_per_layer,
            "fitness": self.fitness,
            "weights": self.weights
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeuralNetIndividual':
        """Deserialize individual from persistence."""
        ind = cls(
            input_size=data["input_size"],
            output_size=data["output_size"],
            num_layers=data["num_layers"],
            neurons_per_layer=data["neurons_per_layer"]
        )
        ind.fitness = data.get("fitness", 0.0)
        ind.weights = data.get("weights", ind._initialize_weights())
        return ind


class EvolutionaryAI:
    """
    The Core Evolutionary Engine handling generation, mutation, and persistence.
    """
    def __init__(self, population_size: int, input_size: int, output_size: int, mutation_rate: float = 0.1):
        self.population_size = population_size
        self.input_size = input_size
        self.output_size = output_size
        self.mutation_rate = mutation_rate
        self.population: List[NeuralNetIndividual] = [
            NeuralNetIndividual(input_size, output_size, random.randint(1, 4), random.randint(8, 64))
            for _ in range(population_size)
        ]
        self.generation = 1
        self.best_fittest: NeuralNetIndividual = None
        self.save_file = "fittest_individual.json"

    def evaluate_fitness(self, individual: NeuralNetIndividual) -> float:
        """
        Abstract fitness evaluation. In practice, this would run the network against training criteria.
        Returns a mock fitness score for demonstration.
        """
        return random.uniform(0, 100)

    def select(self) -> Tuple[NeuralNetIndividual, NeuralNetIndividual]:
        """Tournament selection."""
        tournament = random.sample(self.population, max(2, self.population_size // 5))
        tournament.sort(key=lambda ind: ind.fitness, reverse=True)
        return tournament[0], tournament[1]

    def crossover(self, parent1: NeuralNetIndividual, parent2: NeuralNetIndividual) -> NeuralNetIndividual:
        """
        Mixes architecture parameters between two parents.
        Enforces a hard ceiling on model complexity.
        """
        child_num_layers = random.choice([parent1.num_layers, parent2.num_layers])
        child_neurons = random.choice([parent1.neurons_per_layer, parent2.neurons_per_layer])
        
        # ENFORCE STRICT CEILING (Axiom 3)
        child_num_layers = min(child_num_layers, 4)
        child_neurons = min(child_neurons, 64)
        
        child = NeuralNetIndividual(self.input_size, self.output_size, child_num_layers, child_neurons)
        return child

    def mutate(self, individual: NeuralNetIndividual):
        """
        Mutates the network architecture or weights.
        Enforces a hard ceiling on model complexity to prevent resource hogging.
        """
        if random.random() < self.mutation_rate:
            # Mutate architecture parameters
            individual.num_layers += random.choice([-1, 1])
            individual.neurons_per_layer += random.choice([-8, 8])
            
            # ENFORCE STRICT CEILING (Axiom 3)
            individual.num_layers = max(1, min(individual.num_layers, 4))
            individual.neurons_per_layer = max(1, min(individual.neurons_per_layer, 64))
            
            # Rebuild with new bounds
            individual.build_model(individual.input_size, individual.output_size)
        elif individual.weights:
            # Mutate internal weights
            layer_idx = random.randint(0, len(individual.weights) - 1)
            neuron_idx = random.randint(0, len(individual.weights[layer_idx]) - 1)
            weight_idx = random.randint(0, len(individual.weights[layer_idx][neuron_idx]) - 1)
            
            # Simple mutative adjustment
            individual.weights[layer_idx][neuron_idx][weight_idx] += random.uniform(-0.5, 0.5)

    def evolve_step(self):
        """
        Advances the evolution by one generation. 
        Evaluates fitness, selects parents, applies crossover/mutation.
        """
        # 1. Evaluate current population
        for ind in self.population:
            ind.fitness = self.evaluate_fitness(ind)
            
        # 2. Sort by fitness (descending)
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)
        
        # 3. Update the best fittest individual
        if not self.best_fittest or self.population[0].fitness > self.best_fittest.fitness:
            self.best_fittest = self.population[0]
            
        # 4. Carry over elitist
        new_population = [self.population[0]]
        
        # 5. Breed remaining population
        while len(new_population) < self.population_size:
            p1, p2 = self.select()
            child = self.crossover(p1, p2)
            self.mutate(child)
            new_population.append(child)
            
        self.population = new_population
        self.generation += 1

    def save_fittest(self, filepath: str = None):
        """
        Persists the most fit individual to disk, allowing it to survive reboots.
        Utilizes standard JSON for lightweight persistence.
        """
        path = filepath or self.save_file
        if self.best_fittest:
            try:
                with open(path, 'w') as f:
                    json.dump(self.best_fittest.to_dict(), f, indent=4)
                logger.info(f"Evolutionary Engine: Saved fittest individual to {path}")
            except Exception as e:
                logger.error(f"Evolutionary Engine: Failed to save fittest individual: {e}")

    def load_fittest(self, filepath: str = None) -> bool:
        """
        Retrieves the most fit individual from disk.
        """
        path = filepath or self.save_file
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                self.best_fittest = NeuralNetIndividual.from_dict(data)
                
                # Check for constraints on load to ensure compliance
                self.best_fittest.num_layers = min(self.best_fittest.num_layers, 4)
                self.best_fittest.neurons_per_layer = min(self.best_fittest.neurons_per_layer, 64)
                
                logger.info(f"Evolutionary Engine: Loaded fittest individual from {path}")
                return True
            except Exception as e:
                logger.error(f"Evolutionary Engine: Failed to load fittest individual: {e}")
        return False
