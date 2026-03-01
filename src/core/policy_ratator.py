import random
from src.utils.config_manager import config

class PolicyRotator:

    @staticmethod
    def get_random_policy():
        policies = config.available_policies
        return random.choice(policies)

    @staticmethod
    def get_round_robin_policy(iteration_count):
        policies = config.available_policies
        return policies[iteration_count % len(policies)]