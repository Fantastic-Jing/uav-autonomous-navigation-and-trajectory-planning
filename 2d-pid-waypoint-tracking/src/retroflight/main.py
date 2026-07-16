# --- main.py ---
from retroflight._engine.game import Game
from retroflight._engine.api_server import APIServer

def main():
    print("h_da 2D UAV simulation environment")
    print("Jan Zwiener FBEIT - jan.zwiener@h-da.de")
    print("")
    print("+--------------------------------+-----------------+")
    print("| Key                            | Action          |")
    print("+--------------------------------+-----------------+")
    print("| W / A / S / D or arrow keys    | Move UAV        |")
    print("| Q                              | Ascend          |")
    print("| E                              | Descend         |")
    print("| Escape                         | Quit            |")
    print("+--------------------------------+-----------------+")

    game = Game()

    # Start TCP API Server in the background
    server = APIServer(game.sim)
    server.start()

    # Actual simulation
    game.run()

if __name__ == "__main__":
    main()

