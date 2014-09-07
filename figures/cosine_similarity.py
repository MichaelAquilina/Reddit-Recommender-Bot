from __future__ import division

import math
import numpy as np

from numpy.linalg import norm
from collections import namedtuple
from matplotlib import pyplot as plt
from matplotlib.patches import Arc


def cosine_sim(d1, d2):
    return np.dot(d1, d2) / (norm(d1) * norm(d2))


# http://stackoverflow.com/questions/25227100/best-way-to-plot-an-angle-between-two-lines-in-matplotlib/25228427#25228427
def get_angle_plot(line1, line2, offset=1, color=None, origin=(0, 0), linewidth=1):

    # Angle between line1 and x-axis
    slope1 = line1[1] / line1[0]
    angle1 = abs(math.degrees(math.atan(slope1)))  # Taking only the positive angle

    # Angle between line2 and x-axis
    slope2 = line2[1] / line2[0]
    angle2 = abs(math.degrees(math.atan(slope2)))

    theta1 = min(angle1, angle2)
    theta2 = max(angle1, angle2)

    angle = theta2 - theta1

    if color is None:
        color = 'k'

    return Arc(
        origin, offset, offset,
        0, theta1, theta2, color=color,
        label=str(angle) + u"\u00b0", linewidth=linewidth
    )

point = namedtuple('point', ['x', 'y'])

plt.figure(1, figsize=(10, 5))

plt.ylim([0, 5])
plt.xlim([0, 7])

ax = plt.axes()

arrow_params = {
    'head_width': 0.1,
    'head_length': 0.15,
    'linewidth': 2.0,
}

d = [point(4.5, 3), point(6, 2), point(1, 4)]

ax.arrow(0, 0, d[0].x, d[0].y, fc='k', ec='k', label='d1', **arrow_params)
ax.arrow(0, 0, d[1].x, d[1].y, fc='g', ec='g', label='d2', **arrow_params)
ax.arrow(0, 0, d[2].x, d[2].y, fc='r', ec='r', label='d3', **arrow_params)

arc12 = get_angle_plot(d[0], d[1], offset=2.5, color='g', linewidth=2)
arc13 = get_angle_plot(d[0], d[2], offset=1.5, color='r', linewidth=2)

ax.text(d[0].x + 0.1, d[0].y + 0.1, 'd1', horizontalalignment='left', verticalalignment='bottom')
ax.text(d[1].x + 0.1, d[1].y + 0.1, 'd2', horizontalalignment='left', verticalalignment='bottom')
ax.text(d[2].x + 0.1, d[2].y + 0.1, 'd3', horizontalalignment='left', verticalalignment='bottom')

ax.text(
    5, 4,
    'sim(d1, d2)=%.2f\nsim(d1, d3)=%.2f\nsim(d2, d3)=%.2f' % (
        cosine_sim([4.5, 3], [6, 2]),
        cosine_sim([4.5, 3], [1, 4]),
        cosine_sim([6, 2], [1, 4])
    ),
    fontweight='bold'
)

ax.add_patch(arc12)
ax.add_patch(arc13)

print(cosine_sim([4.5, 3], [6, 2]), cosine_sim([6, 2], [1, 4]))

plt.tight_layout()
plt.gcf().canvas.set_window_title('Cosine Similarity')

plt.show()
