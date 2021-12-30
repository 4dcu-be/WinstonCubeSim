from csv import DictReader as Reader
from random import sample, choice
from rich.console import Console
import readchar
from readchar.key import ENTER, SPACE
import sys

console = Console()


def parse_color(color):
    if len(color) == 1:
        return color
    elif len(color) > 1:
        return 'M'  # Multicolor
    else:
        return 'C'  # Colorless


color_to_rich = {
    'U': 'rgb(14,104,171)',
    'G': 'rgb(0,115,62)',
    'R': 'rgb(211,32,42)',
    'W': 'rgb(248,231,185)',
    'B': 'rgb(166,159,157)',
    'C': 'dark_khaki',
    'M': 'gold1',

}


def render_card(card: dict, current_player: int, show_hidden: bool = False):
    if show_hidden or 'seen' not in card.keys() or card['seen'][current_player]:
        color = color_to_rich[card['color']]
        return f"[{color}]{card['name']}[/{color}]"
    else:
        return "**hidden**"


class CubeData:
    def __init__(self, enable_ai=True):
        self.cards = []
        self.shuffled_cards = []
        self.current_player = 0
        self.current_pile = 0

        self.piles = [[], [], [], ]

        self.players = [[], []]

        self.enable_ai = enable_ai

    @property
    def cards_used(self) -> int:
        return 90 - len(self.shuffled_cards)

    def read_cube_csv(self, filename: str):
        """
        Reads a CSV file with cards, lists from www.cubecobra.com can be exported in this format

        :param filename: path to the file
        """
        self.cards = []

        with open(filename) as csvfile:
            csvreader = Reader(csvfile, delimiter=',', quotechar='"')
            for row in csvreader:
                self.cards.append({
                    'name': row["Name"],
                    'mana_value': int(row["CMC"]),
                    'type': row["Type"],
                    'color': parse_color(row["Color"])
                })

    def reveal_cards(self):
        """
        Sets the 'seen' attribute to true for all cards the current player has seen in this step.
        """
        for c in self.piles[self.current_pile]:
            c['seen'][self.current_player] = True

    def print(self, show_hidden: bool = False):
        """
        Prints the current game to the screen.

        :param show_hidden: if true it will show cards that haven't been seen by the current player
        """
        console.clear()
        console.print(f"Cards in Cube: {len(self.cards)}")
        console.print(f"Cards in main pile/used: {len(self.shuffled_cards)} / {self.cards_used}")
        for i in range(3):
            pile_cards = [render_card(c, self.current_player, show_hidden=show_hidden) for c in self.piles[i]]
            console.print(f"Pile {i + 1}: {', '.join(pile_cards)}", style="bold" if self.current_pile == i else "")
        console.print("")

        for i in range(2):
            style = "bold" if self.current_player == i else ""
            player_cards = [render_card(c, self.current_player, show_hidden=show_hidden) for c in self.players[i]]

            console.print(f"Player {i + 1} ({len(self.players[i])} cards)", style=style)
            console.print(f"Pile {i + 1}: {', '.join(player_cards)}", soft_wrap=True, style=style)

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
        else:
            self.piles[self.current_pile] = []

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
            top_card['seen'][self.current_player] = True
            self.players[self.current_player] += [top_card]

    def prompt_choice(self):
        """
        Asks player to skip the current pile or take it.
        """
        console.print(f"\n\nCurrent player {self.current_player + 1}", style='bold')
        console.print("Press [Space] to skip, [Enter] to take...")
        selection = readchar.readkey()
        if selection == SPACE:
            self.skip()
        elif selection == ENTER:
            self.take_pile()

    def ai_turn(self):
        """
        Let the AI take a turn, currently it will randomly pick a stack (or the top card) based on how many
        cards are in the stack (more cards being more likely to be picked). Not much of an AI but sufficient for
        testing.
        """
        options = []
        for ix, stack in enumerate(self.piles):
            options += [ix] * len(stack)
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

    def start_game(self):
        """
        Start the game
        """
        self.shuffled_cards = sample(self.cards, 90)

        for s in self.shuffled_cards:
            s['seen'] = [False, False]

        self.current_player = 0

        self.piles = [
            [self.shuffled_cards.pop()],
            [self.shuffled_cards.pop()],
            [self.shuffled_cards.pop()],
        ]

        self.players = [[], []]

        # While there are cards on the table, keep going
        while len(self.shuffled_cards) + sum([len(s) for s in self.piles]) > 0:
            # Show current set of cards on the table and selected
            self.reveal_cards()
            self.print()

            # Ask player for choice and act accordingly
            self.prompt_choice()

        # Show final output, reveal all cards from both players
        self.print(show_hidden=True)


if __name__ == '__main__':
    cube_data = CubeData()
    cube_data.read_cube_csv(sys.argv[1])
    cube_data.start_game()
