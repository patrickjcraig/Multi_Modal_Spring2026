from dataclasses import dataclass
import numpy as np


@dataclass
class GLSceneObject:
    name: str
    positions: np.ndarray
    colors: np.ndarray
    point_size: float = 3.0
    visible: bool = True

    def __post_init__(self):
        self.positions = np.asarray(self.positions, dtype=np.float32)
        self.colors = np.asarray(self.colors, dtype=np.float32)

        if self.positions.ndim != 2 or self.positions.shape[1] != 3:
            raise ValueError(f"{self.name}: positions must have shape (N, 3)")

        if self.colors.ndim != 2 or self.colors.shape[1] != 3:
            raise ValueError(f"{self.name}: colors must have shape (N, 3)")

        if self.positions.shape[0] != self.colors.shape[0]:
            raise ValueError(
                f"{self.name}: positions and colors must have the same number of rows"
            )

    def bounds(self):
        if self.positions.shape[0] == 0:
            return np.zeros(3, dtype=np.float32), np.zeros(3, dtype=np.float32)
        return self.positions.min(axis=0), self.positions.max(axis=0)