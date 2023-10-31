import math
from build123d import *
from ocp_vscode import show, Camera

from corne_board import (
    BasePlateSketch,
    MCCoverScrewLocations,
    MCCutoutSketch,
    KeyLocations,
    ScrewLocations,
    POWER_SWITCH_Y_POS,
    RESET_BUTTON_Y_POS,
)

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX

THICKNESS = 6.45
FR = 3
HULL_THICKNESS = 3


class Cover(Part):
    def __init__(self, cols=5, **kwargs):
        kwargs["label"] = kwargs.get("label", "Cover")
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

        self.add_bottom_joint(part)

        super().__init__(part.wrapped, joints=self.joints, **kwargs)

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
        outer_vertices = ShapeList([unfilleted_vertices[i] for i in (0, 3, 5)])
        cover_sk = fillet(outer_vertices, 2.3)

        return cover_sk

    def base_part(self, cover_sk):
        # Extrude into 3D shape
        part = extrude(cover_sk, THICKNESS)

        # fillet top and bottom faces
        bottom = part.edges().group_by(Axis.Z)[0]
        part = fillet(bottom, HULL_THICKNESS)
        top = part.edges().group_by(Axis.Z)[-1]
        part = fillet(top, HULL_THICKNESS)

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
        inner_face = part.faces().filter_by(Axis.Z).group_by(SortBy.AREA)[-2].sort_by(Axis.Z).first
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
        offset = 51
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
        # Reference position based on the MC cover screw locations
        top_face = part.faces().group_by(Axis.Z)[0]
        edge = top_face.edges().filter_by(Axis.Y).sort_by(Axis.X)[1]
        pos = edge.vertices().sort_by(Axis.Y).first.center()
        pos.Y = POWER_SWITCH_Y_POS

        # switch plate dimensions
        depth, width, height, slide_range = HULL_THICKNESS-0.8, 10.2, 2.7, 2.5
        self._switch_plane = plane = Plane(pos, x_dir=(0, 1, 0), z_dir=(1, 0, 0))

        overhang = 0.3
        part -= plane * Box(slide_range * 2, height, HULL_THICKNESS, align=(C, MIN, MAX))
        slide_area = Pos(0, 0, overhang * 2) * Box(
            width, height, overhang + 0.01 + depth, align=(C, MIN, MAX)
        )
        part -= plane * slide_area
        part -= plane * Box(slide_range * 2, height * 2, depth, align=(C, MIN, MAX))

        # Add the linear joint for the switch part to connect to
        joint_axis = Axis(pos - Vector(depth, 0, 0), (0, 1, 0))
        linear_range = [-slide_range/2, slide_range/2]
        joint = LinearJoint("switch_slide", part, axis=joint_axis, linear_range=linear_range)
        self.joints["switch_slide"] = joint

        return part

    def add_button_hole(self, part):
        # Set relative to the switch plane
        pos = self._switch_plane.location.position
        pos.Y = RESET_BUTTON_Y_POS
        plane = Plane(pos, x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        part -= plane * Box(2.7, 2.7, HULL_THICKNESS, align=(C, MIN, MAX))
        part -= plane * Box(4.7, 5.4, 0.01 + HULL_THICKNESS * 0.3, align=(C, MIN, MAX))
        joint_plane = Plane(
            pos - Vector(HULL_THICKNESS * 0.3, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)
        )
        self.joints["button"] = RigidJoint("button", part, joint_location=joint_plane.location)
        return part
    
    def add_bottom_joint(self, part):
        # Add joint for bottom
        bottom_plane = Rotation(about_z=180) * Pos(0, 0, THICKNESS) * Location(-Plane.XY)
        self.joints["bottom"] = RigidJoint("bottom", part, joint_location=Location(bottom_plane))
