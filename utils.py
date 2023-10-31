from build123d import *

def viz_plane(p, size=100):
    square = p * Rectangle(size, size)
    square.color = Color(1, 1, 1, .2)
    x_line = p * Rotation(about_z=-90) * Line((0, 0), (0, size/4))
    x_line.color = Color(1, 0, 0)
    y_line = p * Rotation(about_z=0) * Line((0, 0), (0, size/4))
    y_line.color = Color(0, 1, 0)
    z_line = p * Rotation(about_x=90) * Line((0, 0), (0, size/4))
    z_line.color = Color(0, 0, 1)
    return Compound(children=[square, x_line, y_line, z_line])
