"""
Controller module — lecture temps réel de la manette via pygame
Compatible Xbox, PS4/PS5, manettes génériques USB
"""

import pygame
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ControllerState:
    """Snapshot de l'état de la manette à un instant T"""

    timestamp: float
    # Axes analogiques (valeurs entre -1.0 et 1.0)
    axis_left_x: float = 0.0
    axis_left_y: float = 0.0
    axis_right_x: float = 0.0
    axis_right_y: float = 0.0
    trigger_left: float = 0.0  # 0.0 à 1.0
    trigger_right: float = 0.0  # 0.0 à 1.0
    # Boutons (True = appuyé)
    buttons: dict = field(default_factory=dict)
    # Hat (D-pad)
    hat: tuple = (0, 0)


class Controller:
    """
    Wrapper pygame pour lire une manette en temps réel.
    Détecte automatiquement la première manette branchée.
    """

    # Mapping des axes selon le type de manette (détection automatique)
    AXIS_MAP = {
        "xbox": {"lx": 0, "ly": 1, "rx": 3, "ry": 4, "lt": 2, "rt": 5},
        "ps": {"lx": 0, "ly": 1, "rx": 2, "ry": 3, "lt": 4, "rt": 5},
        "generic": {"lx": 0, "ly": 1, "rx": 2, "ry": 3, "lt": 4, "rt": 5},
    }

    DEADZONE = 0.08  # Ignorer les micro-mouvements

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.controller_type = "generic"
        self._axis_map = self.AXIS_MAP["generic"]
        self._connect()

    def _connect(self) -> bool:
        """Tente de se connecter à la première manette disponible"""
        count = pygame.joystick.get_count()
        if count == 0:
            print("⚠️  Aucune manette détectée. Mode clavier activé.")
            return False

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        name = self.joystick.get_name().lower()
        print(f"🎮 Manette détectée : {self.joystick.get_name()}")

        # Détection automatique du type
        if "xbox" in name or "xinput" in name:
            self.controller_type = "xbox"
        elif "playstation" in name or "dualshock" in name or "dualsense" in name:
            self.controller_type = "ps"
        else:
            self.controller_type = "generic"

        self._axis_map = self.AXIS_MAP[self.controller_type]
        print(f"   Type détecté : {self.controller_type}")
        return True

    def _apply_deadzone(self, value: float) -> float:
        return 0.0 if abs(value) < self.DEADZONE else value

    def get_state(self) -> ControllerState:
        """Retourne un snapshot de l'état actuel de la manette"""
        pygame.event.pump()  # Mise à jour des événements pygame

        if self.joystick is None:
            return ControllerState(timestamp=time.time())

        m = self._axis_map
        num_axes = self.joystick.get_numaxes()

        def safe_axis(idx):
            if idx < num_axes:
                return self._apply_deadzone(self.joystick.get_axis(idx))
            return 0.0

        # Triggers : normalisés de [-1,1] vers [0,1] pour Xbox
        lt_raw = safe_axis(m["lt"])
        rt_raw = safe_axis(m["rt"])
        lt = (lt_raw + 1) / 2 if self.controller_type == "xbox" else lt_raw
        rt = (rt_raw + 1) / 2 if self.controller_type == "xbox" else rt_raw

        buttons = {
            i: bool(self.joystick.get_button(i))
            for i in range(self.joystick.get_numbuttons())
        }

        hat = self.joystick.get_hat(0) if self.joystick.get_numhats() > 0 else (0, 0)

        return ControllerState(
            timestamp=time.time(),
            axis_left_x=safe_axis(m["lx"]),
            axis_left_y=safe_axis(m["ly"]),
            axis_right_x=safe_axis(m["rx"]),
            axis_right_y=safe_axis(m["ry"]),
            trigger_left=lt,
            trigger_right=rt,
            buttons=buttons,
            hat=hat,
        )

    def is_connected(self) -> bool:
        return self.joystick is not None

    def reconnect(self):
        """Tenter une reconnexion (utile si manette branchée après lancement)"""
        pygame.joystick.quit()
        pygame.joystick.init()
        self._connect()
