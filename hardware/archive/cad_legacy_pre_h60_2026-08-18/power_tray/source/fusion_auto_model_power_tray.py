import adsk.core
import adsk.fusion
import traceback


PARAMS = {
    "inner_L": 133.5,
    "inner_W": 75.7,
    "wall_T": 3.0,
    "base_T": 3.0,
    "wall_H": 15.0,
    "slot_L": 30.0,
    "slot_W": 4.0,
    "slot_R": 2.0,
    "slot_margin": 3.0,
    "mount_D": 3.2,
    "mount_offset": 8.0,
    "wall_break_extra": 8.0,
    "fillet_inner": 1.0,
    "fillet_top": 1.0,
    "fillet_slot": 0.6,
    "chamfer_hole": 0.4,
}


def mm(value):
    # Fusion API internal unit is cm.
    return value / 10.0


def add_center_rect(sketch, cx, cy, lx, ly):
    lines = sketch.sketchCurves.sketchLines
    p0 = adsk.core.Point3D.create(mm(cx - lx / 2), mm(cy - ly / 2), 0)
    p1 = adsk.core.Point3D.create(mm(cx + lx / 2), mm(cy - ly / 2), 0)
    p2 = adsk.core.Point3D.create(mm(cx + lx / 2), mm(cy + ly / 2), 0)
    p3 = adsk.core.Point3D.create(mm(cx - lx / 2), mm(cy + ly / 2), 0)
    lines.addByTwoPoints(p0, p1)
    lines.addByTwoPoints(p1, p2)
    lines.addByTwoPoints(p2, p3)
    lines.addByTwoPoints(p3, p0)


def extrude_profiles(root, profiles, distance_mm, operation):
    extrudes = root.features.extrudeFeatures
    obj = adsk.core.ObjectCollection.create()
    for profile in profiles:
        obj.add(profile)
    ext_input = extrudes.createInput(obj, operation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(distance_mm)))
    return extrudes.add(ext_input)


def create_box(root, plane, cx, cy, lx, ly, height_mm, operation):
    sketch = root.sketches.add(plane)
    add_center_rect(sketch, cx, cy, lx, ly)
    return extrude_profiles(root, [sketch.profiles.item(0)], height_mm, operation)


def create_offset_plane(root, base_plane, offset_mm):
    planes = root.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(base_plane, adsk.core.ValueInput.createByReal(mm(offset_mm)))
    return planes.add(plane_input)


def add_obround_slot(sketch, cx, cy, length, width):
    curves = sketch.sketchCurves
    r = width / 2.0
    left_x = cx - length / 2.0 + r
    right_x = cx + length / 2.0 - r
    top_y = cy + r
    bot_y = cy - r

    p_lt = adsk.core.Point3D.create(mm(left_x), mm(top_y), 0)
    p_rt = adsk.core.Point3D.create(mm(right_x), mm(top_y), 0)
    p_rb = adsk.core.Point3D.create(mm(right_x), mm(bot_y), 0)
    p_lb = adsk.core.Point3D.create(mm(left_x), mm(bot_y), 0)
    p_lc = adsk.core.Point3D.create(mm(left_x), mm(cy), 0)
    p_rc = adsk.core.Point3D.create(mm(right_x), mm(cy), 0)

    curves.sketchLines.addByTwoPoints(p_lt, p_rt)
    curves.sketchLines.addByTwoPoints(p_rb, p_lb)
    curves.sketchArcs.addByCenterStartSweep(p_rc, p_rt, -3.141592653589793)
    curves.sketchArcs.addByCenterStartSweep(p_lc, p_lb, -3.141592653589793)


def collect_edges(body, predicate):
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        try:
            if predicate(edge):
                edges.add(edge)
        except Exception:
            pass
    return edges


def edge_sample_point(edge):
    try:
        return edge.pointOnEdge
    except Exception:
        return edge_midpoint(edge)


def edge_midpoint(edge):
    evaluator = edge.evaluator
    ok, p0, p1 = evaluator.getEndPoints()
    if not ok:
        return None
    return adsk.core.Point3D.create(
        (p0.x + p1.x) / 2.0,
        (p0.y + p1.y) / 2.0,
        (p0.z + p1.z) / 2.0,
    )


def add_constant_fillet(root, edges, radius_mm):
    if edges.count == 0:
        return None
    fillets = root.features.filletFeatures
    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(edges, adsk.core.ValueInput.createByReal(mm(radius_mm)), True)
    return fillets.add(fillet_input)


def point_mm(point):
    return point.x * 10.0, point.y * 10.0, point.z * 10.0


def close(a, b, tol=0.05):
    return abs(a - b) <= tol


def in_mount_hole_top_edge(point, p, half_outer_L, half_outer_W):
    x, y, z = point_mm(point)
    if not close(z, p["base_T"], 0.08):
        return False
    centers_x = (-half_outer_L + p["mount_offset"], half_outer_L - p["mount_offset"])
    centers_y = (-half_outer_W + p["mount_offset"], half_outer_W - p["mount_offset"])
    r = p["mount_D"] / 2.0
    for cx in centers_x:
        for cy in centers_y:
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if abs(d - r) <= 0.25:
                return True
    return False


def in_slot_top_edge(point, p, half_outer_W):
    x, y, z = point_mm(point)
    if not close(z, p["base_T"], 0.08):
        return False
    slot_y_abs = half_outer_W - p["slot_margin"] - p["slot_W"] / 2.0
    r = p["slot_W"] / 2.0
    half_len = p["slot_L"] / 2.0
    for cx in (-p["inner_L"] / 4.0, p["inner_L"] / 4.0):
        for cy in (-slot_y_abs, slot_y_abs):
            if cx - half_len - 0.2 <= x <= cx + half_len + 0.2 and cy - r - 0.2 <= y <= cy + r + 0.2:
                return True
    return False


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        if not isinstance(design, adsk.fusion.Design):
            ui.messageBox("Please switch to the Fusion Design workspace first.")
            return

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        p = PARAMS
        outer_L = p["inner_L"] + 2 * p["wall_T"]
        outer_W = p["inner_W"] + 2 * p["wall_T"]
        half_outer_L = outer_L / 2.0
        half_outer_W = outer_W / 2.0
        half_inner_L = p["inner_L"] / 2.0
        half_inner_W = p["inner_W"] / 2.0

        xy = root.xYConstructionPlane

        base = create_box(
            root,
            xy,
            0,
            0,
            outer_L,
            outer_W,
            p["base_T"],
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
        tray_body = base.bodies.item(0)
        tray_body.name = "power_tray_body"

        base_top_plane = create_offset_plane(root, xy, p["base_T"])

        # End walls.
        create_box(root, base_top_plane, -half_inner_L - p["wall_T"] / 2.0, 0, p["wall_T"], outer_W, p["wall_H"],
                   adsk.fusion.FeatureOperations.JoinFeatureOperation)
        create_box(root, base_top_plane, half_inner_L + p["wall_T"] / 2.0, 0, p["wall_T"], outer_W, p["wall_H"],
                   adsk.fusion.FeatureOperations.JoinFeatureOperation)

        # Long side segmented walls.
        break_len = p["slot_L"] + p["wall_break_extra"]
        wall_y = half_inner_W + p["wall_T"] / 2.0
        segments = [
            (-half_inner_L, -p["inner_L"] / 4.0 - break_len / 2.0),
            (-p["inner_L"] / 4.0 + break_len / 2.0, p["inner_L"] / 4.0 - break_len / 2.0),
            (p["inner_L"] / 4.0 + break_len / 2.0, half_inner_L),
        ]
        for side in (-1, 1):
            for x0, x1 in segments:
                create_box(root, base_top_plane, (x0 + x1) / 2.0, side * wall_y, x1 - x0, p["wall_T"], p["wall_H"],
                           adsk.fusion.FeatureOperations.JoinFeatureOperation)

        # Cut strap slots.
        slot_sketch = root.sketches.add(base_top_plane)
        slot_y = half_outer_W - p["slot_margin"] - p["slot_W"] / 2.0
        for x in (-p["inner_L"] / 4.0, p["inner_L"] / 4.0):
            for y in (-slot_y, slot_y):
                add_obround_slot(slot_sketch, x, y, p["slot_L"], p["slot_W"])
        extrude_profiles(root, [slot_sketch.profiles.item(i) for i in range(slot_sketch.profiles.count)],
                         -p["base_T"] - 0.2, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # Cut mounting holes.
        hole_sketch = root.sketches.add(base_top_plane)
        for x in (-half_outer_L + p["mount_offset"], half_outer_L - p["mount_offset"]):
            for y in (-half_outer_W + p["mount_offset"], half_outer_W - p["mount_offset"]):
                hole_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(mm(x), mm(y), 0), mm(p["mount_D"] / 2.0)
                )
        extrude_profiles(root, [hole_sketch.profiles.item(i) for i in range(hole_sketch.profiles.count)],
                         -p["base_T"] - 0.2, adsk.fusion.FeatureOperations.CutFeatureOperation)

        tray_body = root.bRepBodies.item(0)

        # Rounded/soft edges. These selections are intentionally conservative:
        # if Fusion cannot create a fillet, the final message reports it.
        z_top = mm(p["base_T"] + p["wall_H"])
        top_edges = collect_edges(
            tray_body,
            lambda e: (pt := edge_sample_point(e)) is not None and abs(pt.z - z_top) < 1e-4,
        )
        top_count = top_edges.count
        top_fillet_ok = False
        try:
            top_fillet_ok = add_constant_fillet(root, top_edges, p["fillet_top"]) is not None
        except Exception:
            top_fillet_ok = False

        tray_body = root.bRepBodies.item(0)
        slot_or_hole_edges = collect_edges(
            tray_body,
            lambda e: (pt := edge_sample_point(e)) is not None
            and (in_mount_hole_top_edge(pt, p, half_outer_L, half_outer_W) or in_slot_top_edge(pt, p, half_outer_W)),
        )
        slot_hole_count = slot_or_hole_edges.count
        slot_hole_fillet_ok = False
        try:
            slot_hole_fillet_ok = add_constant_fillet(root, slot_or_hole_edges, p["fillet_slot"]) is not None
        except Exception:
            slot_hole_fillet_ok = False

        ui.messageBox(
            "Power tray solid model created. Inspect dimensions, then export STL/STEP from Fusion.\n"
            "Key size: %.1f x %.1f x %.1f mm\n"
            "Top fillet: %s, selected edges: %d, radius: %.1f mm\n"
            "Slot/hole edge fillet: %s, selected edges: %d, radius: %.1f mm"
            % (
                outer_L,
                outer_W,
                p["base_T"] + p["wall_H"],
                "OK" if top_fillet_ok else "NOT CREATED",
                top_count,
                p["fillet_top"],
                "OK" if slot_hole_fillet_ok else "NOT CREATED",
                slot_hole_count,
                p["fillet_slot"],
            )
        )

    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
