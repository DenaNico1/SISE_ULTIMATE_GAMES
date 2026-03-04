"""
ReflexGame — Mini-jeu de réflexe
Des cibles apparaissent à l'écran, le joueur doit appuyer sur le bon bouton
Le plus vite possible. Mesure le temps de réaction et la précision.
"""

import pygame
import random
import time
from games.base_game import BaseGame
from core.controller import ControllerState


# Mapping bouton → couleur + label affiché
BUTTON_CONFIG = {
    0: {"label": "A / Croix", "color": (80, 200, 80), "key": pygame.K_z},
    1: {"label": "B / Rond", "color": (200, 80, 80), "key": pygame.K_x},
    2: {"label": "X / Carré", "color": (80, 80, 200), "key": pygame.K_c},
    3: {"label": "Y / Triangle", "color": (200, 200, 80), "key": pygame.K_v},
}


class ReflexGame(BaseGame):
    """
    Jeu de réflexe : une cible colorée apparaît → le joueur appuie sur
    le bouton correspondant. Score = réussite, malus = mauvais bouton.
    Durée fixe : 60 secondes.
    """

    GAME_DURATION = 60  # secondes
    STIMULUS_INTERVAL = 2.0  # secondes entre les stimuli
    STIMULUS_DISPLAY = 1.5  # secondes d'affichage max

    @property
    def game_id(self) -> str:
        return "reflex"

    def setup(self):
        self.time_elapsed = 0.0
        self.current_target: int | None = None  # Bouton attendu
        self.stimulus_start: float | None = None
        self.next_stimulus_in = 1.0  # Délai avant 1er stimulus
        self.reaction_times = []
        self.correct = 0
        self.wrong = 0
        self._prev_buttons = {}

    def _spawn_stimulus(self):
        """Fait apparaître un nouveau stimulus aléatoire"""
        self.current_target = random.choice(list(BUTTON_CONFIG.keys()))
        self.stimulus_start = time.time()

    def _clear_stimulus(self):
        self.current_target = None
        self.stimulus_start = None
        self.next_stimulus_in = random.uniform(0.8, 2.5)  # Intervalle variable

    def update(self, state: ControllerState, dt: float):
        self.time_elapsed += dt

        # Gestion du timer stimulus
        if self.current_target is None:
            self.next_stimulus_in -= dt
            if self.next_stimulus_in <= 0:
                self._spawn_stimulus()
        else:
            # Stimulus trop long → raté
            if time.time() - self.stimulus_start > self.STIMULUS_DISPLAY:
                self.wrong += 1
                self.recorder.add_score(-5)
                self._clear_stimulus()
                return

            # Détection appui bouton (front montant uniquement)
            for btn_id, pressed in state.buttons.items():
                was_pressed = self._prev_buttons.get(btn_id, False)
                if pressed and not was_pressed:
                    reaction_ms = (time.time() - self.stimulus_start) * 1000
                    if btn_id == self.current_target:
                        self.correct += 1
                        self.reaction_times.append(reaction_ms)
                        # Score bonus selon rapidité
                        bonus = max(10, int(200 - reaction_ms / 5))
                        self.recorder.add_score(bonus)
                    else:
                        self.wrong += 1
                        self.recorder.add_score(-10)
                    self._clear_stimulus()
                    break

            # Fallback clavier (tests sans manette)
            keys = pygame.key.get_pressed()
            keyboard_map = {cfg["key"]: btn_id for btn_id, cfg in BUTTON_CONFIG.items()}
            for key, btn_id in keyboard_map.items():
                if keys[key] and not self._prev_buttons.get(f"kb_{key}", False):
                    if self.current_target is not None:
                        reaction_ms = (time.time() - self.stimulus_start) * 1000
                        if btn_id == self.current_target:
                            self.correct += 1
                            self.reaction_times.append(reaction_ms)
                            bonus = max(10, int(200 - reaction_ms / 5))
                            self.recorder.add_score(bonus)
                        else:
                            self.wrong += 1
                            self.recorder.add_score(-10)
                        self._clear_stimulus()
                    self._prev_buttons[f"kb_{key}"] = True
                else:
                    self._prev_buttons[f"kb_{key}"] = False

        self._prev_buttons = dict(state.buttons)

        # Injection des temps de réaction dans le recorder
        if self.reaction_times:
            avg_rt = sum(self.reaction_times) / len(self.reaction_times)
            self.recorder.reaction_times_avg = avg_rt

    def draw(self, screen: pygame.Surface):
        W, H = self.SCREEN_WIDTH, self.SCREEN_HEIGHT
        font = pygame.font.SysFont("monospace", 28, bold=True)
        font_small = pygame.font.SysFont("monospace", 18)

        # Timer bar
        progress = 1.0 - (self.time_elapsed / self.GAME_DURATION)
        bar_w = int(W * progress)
        pygame.draw.rect(screen, (60, 60, 60), (0, H - 20, W, 20))
        color = (80, 200, 80) if progress > 0.3 else (200, 80, 80)
        pygame.draw.rect(screen, color, (0, H - 20, bar_w, 20))

        # Stats
        rt_avg = (
            sum(self.reaction_times) / len(self.reaction_times)
            if self.reaction_times
            else 0
        )
        stats = [
            f"✅ Corrects : {self.correct}",
            f"❌ Erreurs  : {self.wrong}",
            f"⚡ Réaction : {rt_avg:.0f}ms",
        ]
        for i, s in enumerate(stats):
            surf = font_small.render(s, True, (180, 180, 180))
            screen.blit(surf, (W - 220, 10 + i * 22))

        # Stimulus principal
        if self.current_target is not None:
            cfg = BUTTON_CONFIG[self.current_target]
            elapsed_ratio = (time.time() - self.stimulus_start) / self.STIMULUS_DISPLAY

            # Cercle pulsant
            radius = int(100 + 20 * (1 - elapsed_ratio))
            pygame.draw.circle(screen, cfg["color"], (W // 2, H // 2), radius)
            pygame.draw.circle(screen, (255, 255, 255), (W // 2, H // 2), radius, 3)

            # Label bouton
            label_surf = font.render(cfg["label"], True, (255, 255, 255))
            screen.blit(
                label_surf, (W // 2 - label_surf.get_width() // 2, H // 2 + radius + 20)
            )

            # Barre de temps restant
            time_bar_w = int(200 * (1 - elapsed_ratio))
            pygame.draw.rect(
                screen,
                (255, 150, 0),
                (W // 2 - 100, H // 2 + radius + 60, time_bar_w, 10),
            )
        else:
            # Message d'attente
            wait_surf = font_small.render("Attendez...", True, (80, 80, 100))
            screen.blit(wait_surf, (W // 2 - wait_surf.get_width() // 2, H // 2 - 10))

        # Instructions clavier
        hint = font_small.render(
            "[Z] A  [X] B  [C] X  [V] Y  — ou manette", True, (60, 60, 80)
        )
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 50))

    def is_over(self) -> bool:
        return self.time_elapsed >= self.GAME_DURATION

    def on_game_over(self):
        if self.reaction_times:
            avg = sum(self.reaction_times) / len(self.reaction_times)
            self.recorder.reaction_times_avg = avg
            # Patch : on injecte dans les features calculées plus tard
