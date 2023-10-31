import math

from build123d import *
from build123d.build_common import LocationList


# Defaults
COLS = 6
KEY_SIZE = 14
KEY_MARGIN = Vector(2, 1.5)
STAGGER_OFFSETS = [2, 4.45, 6.8, 4.45, -0.2, -0.2]
KEY_SPACING = Vector(KEY_SIZE + (KEY_MARGIN.X * 2), KEY_SIZE + (KEY_MARGIN.Y * 2))
SCREW_RADIUS = 1.2
POWER_SWITCH_Y_POS = 6.5
RESET_BUTTON_Y_POS = 15


class KeyLocations(LocationList):
    def __init__(self, cols=6):
        locations = []
        norm = Vector(0, 0, 1)

        # Thumb keys
        locations.append(Location(Vector(14.8, -10.8), norm, 30))
        locations.append(Location(Vector(35, -7.2), norm, 15))
        locations.append(Location(Vector(54.8, -4.5), norm, 0))

        # Grid keys
        start_x = 27.5
        for row in range(0, 3):
            baseline = KEY_MARGIN.Y + KEY_SIZE / 2 + (KEY_SPACING.Y * row)
            for col in range(0, cols):
                pos = Vector(
                    start_x + (KEY_SPACING.X * col),
                    baseline + STAGGER_OFFSETS[col],
                )
                locations.append(Location(pos, norm, 0))

        local_locations = Locations._move_to_existing(locations)
        super().__init__(local_locations)


class ScrewLocations(LocationList):
    def __init__(self, cols=6):
        positions = [
            Vector((23.05, -4.55)),
            Vector((67.6, 2.1)),
            Vector((108.50, 16.8)),
            Vector((108.50, 33.75)),
            Vector((36.50, 37.2)),
        ]
        if cols == 5:
            positions[2].X -= KEY_SPACING.X
            positions[3].X -= KEY_SPACING.X
        locations = [Location(v) for v in positions]
        local_locations = Locations._move_to_existing(locations)
        super().__init__(local_locations)


class BasePlateLine(Curve):
    def __init__(self, cols=6):
        ln = Curve()
        y = (3 * ((KEY_MARGIN.Y * 2) + KEY_SIZE)) + STAGGER_OFFSETS[0]
        ln += Line((-0.8, -1), (-0.8, y))
        ln += Line(ln @ 1, ln @ 1 + Vector(18.5, 0))
        for col in range(1, cols):
            seg_width = (KEY_MARGIN.X * 2) + KEY_SIZE
            if col == 1:
                seg_width += 1
            elif col == 3:
                seg_width -= 1
            ln += Line(ln @ 1, ln @ 1 + Vector(seg_width, 0))
            y = STAGGER_OFFSETS[col] - STAGGER_OFFSETS[col - 1]
            if abs(y) > 0:
                ln += Line(ln @ 1, ln @ 1 + Vector(0, y))
        ln += Line(ln @ 1, ln @ 1 + Vector(seg_width + 1.8, 0))
        ln += Line(ln @ 1, ((ln @ 1).X, -0.5))
        dx = (seg_width * (cols - 3)) + 1.5
        ln += Line(ln @ 1, ln @ 1 + Vector(-dx, 0))
        ln += Line(ln @ 1, ln @ 1 + Vector(-9, -12.2))
        ln += Line(ln @ 1, ln @ 1 + Vector(-33.1, -4.55))
        ln += Line(ln @ 1, ln @ 1 + Vector(-16.35, -9.12))
        ln += Line(ln @ 1, ln @ 0)
        super().__init__(ln.wrapped)


class BasePlateSketch(Sketch):
    def __init__(self, cols=6, screw_radius=SCREW_RADIUS, do_fillet=True):
        sk = Sketch()
        ln = BasePlateLine(cols=cols)
        sk = make_face(ln)
        if do_fillet:
            sk = fillet(sk.vertices(), radius=1)
        if screw_radius:
            for loc in ScrewLocations(cols=cols):
                sk -= loc * Circle(screw_radius)
        super().__init__(sk.wrapped)


class MCCutoutSketch(Sketch):
    def __init__(self):
        start = Vector(-0.85, 53)
        ln = Line(start, start + Vector(19.3, 0))
        ln += Line(ln @ 1, ln @ 1 + Vector(0, -48.31))
        ln += Line(ln @ 1, ln @ 1 + Vector(-3.25, 0))
        ln += Line(ln @ 1, ln @ 1 + Vector(-16.05, -16.05 * math.tan(math.radians(30))))
        ln += Line(ln @ 1, ln @ 0)
        sk = make_face(ln)
        super().__init__(sk.wrapped)


class MCCoverScrewLocations(LocationList):
    def __init__(self):
        positions = [
            Vector((1.8, .4)),
            Vector((15.5, 7.6))
        ]
        locations = [Location(v) for v in positions]
        local_locations = Locations._move_to_existing(locations)
        super().__init__(local_locations)


class KeyPlateSketch(Sketch):
    def __init__(
        self,
        cols=COLS,
        key_size=KEY_SIZE - 0.2,
        screw_radius=SCREW_RADIUS,
        cut_display=True,
        do_fillet=True
    ):
        self.cols = cols
        sk = BasePlateSketch(cols=cols, do_fillet=do_fillet)
        vertices = sk.vertices()
        if cut_display:
            sk = self.cut_display_area(sk)
        new_vertices = sk.vertices() - vertices
        if new_vertices and do_fillet:
            sk = fillet(new_vertices, 1)
        sk = self.make_key_holes(sk, key_size)
        if screw_radius:
            sk = self.make_screw_holes(sk, screw_radius)
        super().__init__(sk.wrapped)

    def cut_display_area(self, sketch):
        sketch -= MCCutoutSketch()
        return sketch

    def make_key_holes(self, sketch, key_size):
        for loc in KeyLocations(cols=self.cols):
            sketch -= loc * Rectangle(
                key_size, key_size, align=(Align.CENTER, Align.CENTER)
            )
        return sketch

    def make_screw_holes(self, sketch, screw_radius):
        for loc in ScrewLocations(cols=self.cols):
            sketch -= loc * Circle(screw_radius)
        return sketch
