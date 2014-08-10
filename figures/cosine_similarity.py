from collections import namedtuple
from matplotlib import pyplot as plt

point = namedtuple('point', ['x', 'y'])

plt.ylim([0, 5])
plt.xlim([0, 7])

arrow_params = {
    'head_width': 0.1,
    'head_length': 0.15,
    'linewidth': 2.0,
}

d = [point(4.5, 3), point(6, 2), point(1, 4)]

plt.arrow(0, 0, d[0].x, d[0].y, fc='b', ec='b', label='d1', **arrow_params)
plt.arrow(0, 0, d[1].x, d[1].y, fc='g', ec='g', label='d2', **arrow_params)
plt.arrow(0, 0, d[2].x, d[2].y, fc='r', ec='r', label='d3', **arrow_params)

plt.text(d[0].x + 0.1, d[0].y + 0.1, 'd1', horizontalalignment='left', verticalalignment='bottom')
plt.text(d[1].x + 0.1, d[1].y + 0.1, 'd2', horizontalalignment='left', verticalalignment='bottom')
plt.text(d[2].x + 0.1, d[2].y + 0.1, 'd3', horizontalalignment='left', verticalalignment='bottom')

plt.gcf().canvas.set_window_title('Cosine Similarity')

plt.show()
