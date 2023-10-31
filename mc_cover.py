import math
from build123d import *

from corne_board import MCCoverScrewLocations, MCCutoutSketch
from params import FR, HULL_THICKNESS, MC_COVER_HEIGHT

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX
TOP_THICKNESS = 1.8
DISPLAY_OFFSET_X = 3
DISPLAY_OFFSET_Y = 10


class MCCoverSketch(Sketch):
    def __init__(self):
        # Add MC cover portion, flat on top
        sk = MCCutoutSketch()
        bbox = sk.bounding_box()

        # extend edges
        offset = HULL_THICKNESS
        bot = sk.vertices().sort_by(Axis.Y).first.to_vector()
        ln = Line(bot, bot + Vector(-offset, -offset * math.tan(math.radians(30))))
        ln += Line(ln @ 1, Vector((ln @ 1).X, bbox.max.Y + offset))
        ln += Line(ln @ 1, Vector(bbox.max.X, (ln @ 1).Y))
        ln += Line(ln @ 1, Vector(bbox.max.X, bbox.max.Y))
        ln += sk.edges().filter_by(Axis.X).sort_by(Axis.Y).last.to_wire()
        ln += sk.edges().filter_by(Axis.Y).sort_by(Axis.X).first.to_wire()

        sk += make_face(ln)

        # round corners
        sk = fillet(sk.vertices().group_by(Axis.Y)[-1].sort_by(Axis.X).first, FR)
        sk = fillet(sk.vertices().group_by(Axis.Y)[0].sort_by(Axis.X).first, FR)

        super().__init__(sk.wrapped)


class MCCoverCutoutSketch(Sketch):
    def __init__(self):
        sk = MCCutoutSketch()
        bbox = sk.bounding_box()
        offset = 51
        sk -= Pos(bbox.max.X, bbox.max.Y) * Rectangle(
            bbox.size.X, bbox.size.Y - offset, align=(MAX, MAX)
        )
        sk = Pos(0, bbox.size.Y - offset) * sk

        super().__init__(sk.wrapped)


class MCCover(Part):
    def __init__(self, **kwargs):
        kwargs["label"] = kwargs.get("label", "MC/display cover")
        sk = MCCoverSketch()
        part = extrude(sk, MC_COVER_HEIGHT)
        top_edges = part.edges().group_by(Axis.Z)[-1]
        top_right = top_edges.vertices().group_by(Axis.X)[-1].sort_by(Axis.Y).last.center()
        exclude = ShapeList([top_edges.filter_by(Axis.Y).sort_by(Axis.X).last])
        part = fillet(top_edges - exclude, FR)
        part -= extrude(MCCoverCutoutSketch(), MC_COVER_HEIGHT - TOP_THICKNESS)
        # show(part, reset_camera=Camera.KEEP)
        # raise Exception

        # chamfer right edge
        right_edges = part.edges().group_by(Axis.X)[-1]
        chamf_edges = ShapeList()
        chamf_edges += ShapeList([right_edges.sort_by(Axis.Z).last])
        chamf_edges += ShapeList([right_edges.filter_by(Axis.Z).sort_by(Axis.Y).first])
        chamf_edges += ShapeList([right_edges.filter_by(Axis.Z).sort_by(Axis.Y).last])
        chamf_edges += right_edges.filter_by(GeomType.CIRCLE)
        part = chamfer(chamf_edges, 0.5)

        # cut display hole
        top_face = part.faces().sort_by(Axis.Z).last
        display_plane = Plane(top_face).shift_origin(
            top_right - Vector(DISPLAY_OFFSET_X, DISPLAY_OFFSET_Y, 0)
        )
        display_hole = display_plane * Rectangle(12, 26.5, align=(MIN, MIN))
        display_inset = display_plane * Pos(-1.25, -5) * Rectangle(14.5, 37.25, align=(MIN, MIN))
        part -= extrude(display_hole, -TOP_THICKNESS)
        part -= extrude(Pos(0, 0, -0.4) * display_inset, -1.8)

        # cut USB-C port hole
        back_face = part.faces().sort_by(Axis.Y).last
        plane = Plane(back_face)
        sk = plane * Rectangle(10.2, 4.4)
        sk = fillet(sk.vertices(), 2.2)
        part -= extrude(sk, -4)

        # chamfer hole edges
        top = part.edges().group_by(Axis.Z)[-1]
        chamf_edges = ShapeList(top.filter_by(Axis.Y).sort_by(Axis.X)[1:3])
        chamf_edges += ShapeList(top.filter_by(Axis.X).sort_by(Axis.Y)[1:3])
        part = chamfer(chamf_edges, 0.39)

        # Cut screw holes
        part -= Plane.XY * MCCoverScrewLocations() * extrude(Circle(1.2), 4.9)
        joint_location = MCCoverScrewLocations().locations[0]
        joint = RigidJoint("joint", part, joint_location=joint_location)

        # Mirror
        part = mirror(part, about=Plane.XY)

        super().__init__(part.wrapped, joints={"joint": joint}, **kwargs)
