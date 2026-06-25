import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

# figura
fig, ax = plt.subplots(figsize=(8,3))

ax.set_facecolor("#0f172a")
fig.patch.set_facecolor("#0f172a")

ax.set_xlim(0, 10)
ax.set_ylim(-1.5, 1.5)

ax.grid(alpha=0.3)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

line, = ax.plot(
    [],
    [],
    linewidth=3,
    color="cyan"
)

x = np.linspace(0, 10, 1000)

def update(frame):

    y = np.sin(x + frame * 0.1)
    """y = (
    np.sin(x + frame*0.1)
    + 0.3*np.sin(5*x)
    + 0.15*np.sin(12*x)
    )"""

    line.set_data(x, y)

    return line,

anim = FuncAnimation(
    fig,
    update,
    frames=100,
    interval=30,
    blit=True
)

anim.save(
    "assets/senoide.gif",
    writer=PillowWriter(fps=60)
)

plt.close()