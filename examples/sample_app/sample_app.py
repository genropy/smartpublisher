"""
Sample application for smpub examples.

Example of a multi-handler app using smpub Publisher.
"""

import sys
sys.path.insert(0, '../../src')

from classes.L1_alpha import L1_alpha
from classes.L1_beta import L1_beta
from classes.L1_gamma import L1_gamma
from smpub import Publisher


class MainClass(Publisher):
    """Main application class."""

    def initialize(self):
        self.alfa_handler = L1_alpha()
        self.beta_handler = L1_beta()
        self.gamma_handler = L1_gamma()

        self.publish('alfa', self.alfa_handler)
        self.publish('beta', self.beta_handler)
        self.publish('gamma', self.gamma_handler)


if __name__ == "__main__":
    app = MainClass()
    app.run()
