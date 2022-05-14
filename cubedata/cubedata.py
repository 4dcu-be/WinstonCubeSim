from csv import DictReader as Reader
from random import sample, choice


def parse_color(color):
    if len(color) == 1:
        return color
    elif len(color) > 1:
        return "M"  # Multicolor
    else:
        return "C"  # Colorless


class CubeData:
    def __init__(self, enable_ai: bool = True, draft_size: int = 90):
        self.cards = []
        self.shuffled_cards = []
        self.unused_cards = []
        self.current_player = 0
        self.current_pile = 0

        self.piles = [
            [],
            [],
            [],
        ]

        self.players = [[], []]

        self.draft_size = draft_size

        self.enable_ai = enable_ai
        self.pile_width = 40

    @property
    def cards_used(self) -> int:
        return self.draft_size - len(self.shuffled_cards)

    @property
    def card_count(self) -> int:
        return len(self.cards)

    def read_cube_csv(self, filename: str):
        """
        Reads a CSV file with cards, lists from www.cubecobra.com can be exported in this format

        :param filename: path to the file
        """
        self.cards = []

        with open(filename) as csvfile:
            csvreader = Reader(csvfile, delimiter=",", quotechar='"')
            for row in csvreader:
                self.cards.append(
                    {
                        "name": row["Name"],
                        "mana_value": int(row["CMC"]),
                        "type": row["Type"],
                        "color": parse_color(row["Color"]),
                    }
                )

    def reveal_cards(self):
        """
        Sets the 'seen' attribute to true for all cards the current player has seen in this step.
        """
        for c in self.piles[self.current_pile]:
            c["seen"][self.current_player] = True

    def switch_player(self):
        """
        Switches the current player, in case the AI is enabled the AI-player's turn is started here
        """
        self.current_player = 1 if self.current_player == 0 else 0

        if self.enable_ai and self.current_player == 1:
            self.ai_turn()

    def pop_to_current(self):
        """
        Moves the top card of the deck to the current pile
        """
        if len(self.shuffled_cards) > 0:
            self.piles[self.current_pile] += [self.shuffled_cards.pop()]

    def skip(self):
        """
        Current player doesn't want the current pile, move to the next or take the top card of the deck
        """
        self.pop_to_current()
        if self.current_pile < 2:
            self.current_pile += 1
        else:
            # skip on the last pile so take top card of deck
            self.current_pile = 0
            self.take_top_card()
            self.switch_player()

    def take_pile(self):
        """
        Takes the current pile and moves it into the current player's selection
        """
        self.players[self.current_player] += self.piles[self.current_pile]
        self.piles[self.current_pile] = []

        self.pop_to_current()
        self.current_pile = 0

        self.switch_player()

    def take_top_card(self):
        """
        Takes the top card of the deck and moves it to the current player's selection
        """
        if len(self.shuffled_cards) > 0:
            top_card = self.shuffled_cards.pop()
            top_card["seen"][self.current_player] = True
            self.players[self.current_player] += [top_card]

    def ai_turn(self):
        """
        Let the AI take a turn, currently it will randomly pick a stack (or the top card) based on how many
        cards are in the stack (more cards being more likely to be picked). Not much of an AI but sufficient for
        testing.
        """
        options = []
        for ix, stack in enumerate(self.piles):
            options += [ix] * len(stack)

        # If there are cards in the main pile there is chance the AI will pick that
        if 0 < len(self.shuffled_cards):
            options += [3]

        selected_option = choice(options)

        if selected_option == 0:
            self.take_pile()
        elif selected_option == 1:
            self.skip()
            self.take_pile()
        elif selected_option == 2:
            self.skip()
            self.skip()
            self.take_pile()
        elif selected_option == 3:
            self.skip()
            self.skip()
            self.skip()

    def shuffle_cards(self):
        temp_pile = sample(self.cards, len(self.cards))
        self.shuffled_cards = temp_pile[: self.draft_size]
        self.unused_cards = temp_pile[self.draft_size :]

        for s in self.shuffled_cards:
            s["seen"] = [False, False]
