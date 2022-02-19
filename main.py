import curses
from game import Game


def main():
    game = Game(debug=True)
    curses.wrapper(game.run)


if __name__ == '__main__':
    main()
