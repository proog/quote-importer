"""Write nothing for dry runs"""


class DryRun:
    def max_sequence_id(self, channel):
        return 0

    def insert_all(self, quotes):
        print("Dry run: would have inserted %i" % len(quotes))

    def initialize(self):
        pass

    def close(self):
        pass
