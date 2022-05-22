from .cubedata import CubeData

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress_bar import ProgressBar
import readchar
from readchar.key import ENTER, SPACE
from itertools import zip_longest

console = Console()


color_to_rich = {
    "U": "rgb(14,104,171)",
    "G": "rgb(0,115,62)",
    "R": "rgb(211,32,42)",
    "W": "rgb(248,231,185)",
    "B": "rgb(166,159,157)",
    "C": "dark_khaki",
    "M": "gold1",
}


def render_card(card: dict, current_player: int, show_hidden: bool = False):
    if show_hidden or "seen" not in card.keys() or card["seen"][current_player]:

        color = color_to_rich[card["color"]]

        return f"[{color}]{card['name']}[/{color}]"
    else:
        return "**hidden**"


class RichCubeData(CubeData):
    def __init__(self, enable_ai: bool = True, draft_size: int = 90):
        self.pile_width = 40
        super().__init__(enable_ai, draft_size)

    def print_stats(self):
        console.print(f"Cards in Cube: {len(self.cards)}")
        console.print(
            f"Cards in main pile/used: {len(self.shuffled_cards)} / {self.cards_used}"
        )

        console.print("")

    def print_piles(self, show_hidden: bool = False):
        piles_table = Table(
            title=f"Current Pile : {self.current_pile+1}", title_style="bold"
        )
        piles_table.add_column(
            "Pile 1",
            style="bold" if self.current_pile == 0 else "",
            min_width=self.pile_width,
            max_width=self.pile_width,
        )
        piles_table.add_column(
            "Pile 2",
            style="bold" if self.current_pile == 1 else "",
            min_width=self.pile_width,
            max_width=self.pile_width,
        )
        piles_table.add_column(
            "Pile 3",
            style="bold" if self.current_pile == 2 else "",
            min_width=self.pile_width,
            max_width=self.pile_width,
        )

        for c1, c2, c3 in zip_longest(*self.piles, fillvalue=None):
            piles_table.add_row(
                render_card(c1, self.current_player, show_hidden=show_hidden)
                if c1 is not None
                else "",
                render_card(c2, self.current_player, show_hidden=show_hidden)
                if c2 is not None
                else "",
                render_card(c3, self.current_player, show_hidden=show_hidden)
                if c3 is not None
                else "",
            )

        for _ in range(len(piles_table.rows), 10, 1):
            piles_table.add_row(None, None, None)

        console.print(piles_table)
        console.print("")

    def print_players(self, show_hidden: bool = False):
        for i in range(2):

            style = "bold" if self.current_player == i else ""
            player_cards = [
                render_card(c, self.current_player, show_hidden=show_hidden)
                for c in self.players[i]
            ]

            panel_title = f"Player {i + 1} ({len(self.players[i])} cards)"
            panel_content = ", ".join(player_cards)

            panel = Panel(
                panel_content,
                title=panel_title,
                style=style,
                width=self.pile_width * 3 + 10,
            )

            console.print(panel)
            console.print("")

    def print_unused_cards(self):
        unused_cards = [render_card(c, 0, show_hidden=True) for c in self.unused_cards]

        panel_title = f"Unused cards ({len(self.unused_cards)} cards)"
        panel_content = ", ".join(unused_cards)

        panel = Panel(panel_content, title=panel_title, width=self.pile_width * 3 + 10)

        console.print(panel)

    def print_progress(self):
        total_cards_picked = sum([len(p) for p in self.players])
        progress_bar = ProgressBar(
            total=self.draft_size,
            completed=total_cards_picked,
            width=self.pile_width * 3 + 10,
        )

        console.print(progress_bar)
        console.print()

    def print(
        self,
        show_hidden: bool = False,
        show_piles: bool = True,
        show_unused: bool = False,
    ):
        """
        Prints the current game to the screen.

        :param show_hidden: if true it will show card names that haven't been seen by the current player
        :param show_piles: if true will show piles of cards available, only hide after playing
        :param show_unused: if true cards not used this game will be shown
        """
        console.clear()

        self.print_stats()

        self.print_progress()

        if show_piles:
            self.print_piles(show_hidden=show_hidden)

        self.print_players(show_hidden=show_hidden)

        if show_unused:
            self.print_unused_cards()

    def prompt_choice(self):
        """
        Asks player to skip the current pile or take it.
        """
        console.print(f"Current player {self.current_player + 1}", style="bold")
        console.print(
            f"Press [Space] to skip, [Enter] to take [bold]pile {self.current_pile+1}[/bold]..."
        )
        selection = readchar.readkey()
        if selection == SPACE:
            self.skip()
        elif selection == ENTER:
            self.take_pile()

    def start_game(self):
        """
        Start the game
        """
        self.init_game()

        # While there are cards on the table, keep going
        while len(self.shuffled_cards) + sum([len(s) for s in self.piles]) > 0:
            # Show current set of cards on the table and selected
            self.reveal_cards()
            self.print()

            # Ask player for choice and act accordingly
            self.prompt_choice()

        # Show final output, reveal all cards from both players
        self.print(show_hidden=True, show_unused=True, show_piles=False)
