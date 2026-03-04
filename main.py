"""
SISE ULTIMATE — Point d'entrée principal
Usage :
  python main.py --player Alice --game reflex
  python main.py --player Bob   --game labyrinth
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="SISE ULTIMATE — IA Temps Réel")
    parser.add_argument("--player", type=str, default="Player1", help="Nom du joueur")
    parser.add_argument(
        "--game",
        type=str,
        default="reflex",
        choices=["reflex", "labyrinth"],
        help="Jeu à lancer",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Mode sans fenêtre (tests)"
    )
    args = parser.parse_args()

    # Import tardif pour éviter pygame au niveau module
    if args.game == "reflex":
        from games.reflex_game import ReflexGame as GameClass
    elif args.game == "labyrinth":
        from games.labyrinth_game import LabyrinthGame as GameClass

    game = GameClass(player_name=args.player, headless=args.headless)
    features = game.run()

    print("\n📊 Features extraites :")
    for k, v in vars(features).items():
        print(f"   {k:30s} : {v}")


if __name__ == "__main__":
    main()
