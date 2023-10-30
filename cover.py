import math
from build123d import *

from corne_board import (
    BasePlateSketch,
    MCCoverScrewLocations,
    MCCutoutSketch,
    KeyLocations,
    ScrewLocations,
)

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX

THICKNESS = 6.45
FR = 3
HULL_THICKNESS = 2


class Cover(Part):
    def __init__(self, cols=5):
        self.cols = cols
        self._base_plate_sk = BasePlateSketch(
            cols=self.cols, do_fillet=False, screw_radius=0
        )
        self.joints = {}
        sk = self.make_base_sk()
        part = self.base_part(sk)
        part = self.cut_inset(part)
        part = self.add_keys(part)
        part = self.cut_display(part)
        part = self.add_screw_holes(part)
        part = self.add_switch_hole(part)
        part = self.add_button_hole(part)

        super().__init__(part.wrapped, joints=self.joints)

    def make_base_sk(self):
        # Thicken by FR, then round corners by same amount
        cover_sk = offset(self._base_plate_sk, HULL_THICKNESS, kind=Kind.INTERSECTION)

        # Round out corners
        fillet_vertices = []
        for v in cover_sk.vertices():
            edges = [e for e in cover_sk.edges() if v in e.vertices()]
            if all(e.length > FR for e in edges):
                fillet_vertices.append(v)
        orig_vertices = cover_sk.vertices()
        cover_sk = fillet(fillet_vertices, FR)
        unfilleted_vertices = cover_sk.vertices() - (
            cover_sk.vertices() - orig_vertices
        )

        # FIXME: find a way to only select "outer" corners, this can break easily
        unfilleted_vertices = unfilleted_vertices.sort_by(Axis.Y).sort_by(Axis.X)
        outer_vertices = ShapeList([unfilleted_vertices[i] for i in (1, 3, 5)])
        cover_sk = fillet(outer_vertices, 2.3)

        return cover_sk

    def base_part(self, cover_sk):
        # Extrude into 3D shape
        part = extrude(cover_sk, THICKNESS)

        # fillet top and bottom faces
        bottom = part.edges().group_by(Axis.Z)[0]
        part = fillet(bottom, 3)
        top = part.edges().group_by(Axis.Z)[-1]
        part = fillet(top, 3)

        # Add MC cover portion, flat on top
        sk = MCCutoutSketch()
        bbox = sk.bounding_box()

        # extend edges
        offset = HULL_THICKNESS
        bot = sk.vertices().sort_by(Axis.Y).first.to_vector()
        top = sk.vertices().group_by(Axis.Y)[-1].sort_by(Axis.X).first.to_vector()
        ln = Line(bot, bot + Vector(-offset, -offset * math.tan(math.radians(30))))
        ln += Line(ln @ 1, Vector((ln @ 1).X, bbox.max.Y + offset))
        ln += Line(ln @ 1, Vector(bbox.max.X, (ln @ 1).Y))
        ln += Line(ln @ 1, Vector(bbox.max.X, bbox.max.Y))
        ln += sk.edges().filter_by(Axis.X).sort_by(Axis.Y).last.to_wire()
        ln += sk.edges().filter_by(Axis.Y).sort_by(Axis.X).first.to_wire()

        sk += make_face(ln)

        # round corners
        sk = fillet(sk.vertices().group_by(Axis.Y)[-1], FR)
        sk = fillet(sk.vertices().group_by(Axis.Y)[0].sort_by(Axis.X).first, FR)

        # Add the MC window shape to the overall shape
        part += extrude(sk, THICKNESS / 2)

        return part

    def cut_inset(self, part):
        # Cut the board inset
        top = part.faces().sort_by(Axis.Z).sort_by(SortBy.AREA)[-2]
        inset_sk = Plane((0, 0, top.center().Z)) * self._base_plate_sk
        part -= extrude(inset_sk, -4.5)
        inner_face = (
            part.faces().filter_by(Axis.Z).sort_by(Axis.Z).sort_by(SortBy.AREA).last
        )
        self._inset_plane = Plane((0, 0, inner_face.center().Z))
        return part

    def add_keys(self, part):
        # Cut out key holes (inset)
        key_locations = self._inset_plane * KeyLocations(cols=self.cols)
        part -= key_locations * extrude(Rectangle(15.5, 15.5, align=(C, C)), -0.8)
        part -= key_locations * extrude(Rectangle(13.5, 13.7, align=(C, C)), -2.1)
        return part

    def cut_display(self, part):
        # Cut out MC display hole
        sk = MCCutoutSketch()
        bbox = sk.bounding_box()
        offset = 53
        sk -= Pos(bbox.max.X, bbox.max.Y) * Rectangle(
            bbox.size.X, bbox.size.Y - offset, align=(MAX, MAX)
        )
        sk = Pos(0, bbox.size.Y - offset) * sk
        part -= extrude(sk, THICKNESS)
        return part

    def add_screw_holes(self, part):
        # Add screw holes
        part -= (
            self._inset_plane
            * ScrewLocations(cols=self.cols)
            * CounterBoreHole(1.2, 2.15, 0.8, THICKNESS / 2)
        )
        part -= MCCoverScrewLocations() * extrude(Circle(1.2), THICKNESS)
        return part

    def add_switch_hole(self, part):
        # Add switch
        top_face = part.faces().group_by(Axis.Z)[0]
        edge = top_face.edges().filter_by(Axis.Y).sort_by(Axis.X)[1]
        rel_pos = edge.vertices().sort_by(Axis.Y).first.center()

        # switch plate dimensions
        depth, width, height, slide_range = 1.2, 10.2, 2.7, 2.5

        pos = rel_pos + Vector(0, 1.65 + width/2, 0)
        self._switch_plane = plane = Plane(pos, x_dir=(0, 1, 0), z_dir=(1, 0, 0))

        part -= plane * Box(slide_range * 2, height, HULL_THICKNESS, align=(C, MIN, MAX))
        part -= plane * Box(width, height, depth, align=(C, MIN, MAX))
        part -= plane * Box(slide_range * 2, height * 2, depth, align=(C, MIN, MAX))

        # Add the linear joint for the switch part to connect to
        joint_axis = Axis(pos - Vector(depth, 0, 0), (0, 1, 0))
        linear_range = [-slide_range/2, slide_range/2]
        joint = LinearJoint("switch_slide", part, axis=joint_axis, linear_range=linear_range)
        self.joints["switch_slide"] = joint

        return part

    def add_button_hole(self, part):
        # Set relative to the switch plane
        pos = self._switch_plane.location.position + Vector(0, 8, 0)
        plane = Plane(pos, x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        part -= plane * Box(2.7, 2.7, HULL_THICKNESS, align=(C, MIN, MAX))
        part -= plane * Box(4.7, 5.4, 1.2, align=(C, MIN, MAX))
        joint_plane = Plane(pos - Vector(1.2, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        self.joints["button"] = RigidJoint("button", part, joint_location=joint_plane.location)
        return part
