"""
Sample application for smpub examples.

Example of a multi-handler app using smpub Publisher.
"""

import sys

sys.path.insert(0, "../../src")

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

        # Publish handlers with custom CLI names and HTTP paths
        self.publish("alfa", self.alfa_handler, cli_name="alfa", http_path="/api/alfa")
        self.publish("beta", self.beta_handler, cli_name="beta", http_path="/api/beta")
        self.publish("gamma", self.gamma_handler, cli_name="gamma", http_path="/api/gamma")


if __name__ == "__main__":
    app = MainClass()
    app.run()
