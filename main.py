"""
SISE ULTIMATE — Point d'entrée principal
Lance un mini-jeu pour un joueur donné.
"""

import sys
import argparse
from games.reflex_game import ReflexGame


def main():
    parser = argparse.ArgumentParser(description="SISE ULTIMATE — IA Temps Réel")
    parser.add_argument("--player", type=str, default="Player1", help="Nom du joueur")
    parser.add_argument(
        "--game", type=str, default="reflex", help="Jeu à lancer (reflex, ...)"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Mode sans fenêtre (tests)"
    )
    args = parser.parse_args()

    GAMES = {
        "reflex": ReflexGame,
        # "labyrinth": LabyrinthGame,  # À ajouter plus tard
        # "rhythm":    RhythmGame,
    }

    if args.game not in GAMES:
        print(f"❌ Jeu inconnu : {args.game}. Disponibles : {list(GAMES.keys())}")
        sys.exit(1)

    GameClass = GAMES[args.game]
    game = GameClass(player_name=args.player, headless=args.headless)
    features = game.run()

    print("\n📊 Features extraites :")
    for k, v in vars(features).items():
        print(f"   {k:30s} : {v}")


if __name__ == "__main__":
    main()
