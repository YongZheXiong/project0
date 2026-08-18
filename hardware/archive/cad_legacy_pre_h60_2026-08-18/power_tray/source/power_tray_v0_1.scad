// Project0 power battery tray, design draft v0.1
// Units: millimeters.
// This source is intended for review and parametric editing.

$fn = 64;

battery_length = 132.0;
battery_width = 67.7;
battery_height = 56.0;

inner_length = 133.5;
inner_width = 75.7;
wall_thickness = 3.0;
base_thickness = 3.0;
wall_height = 15.0;

outer_length = inner_length + wall_thickness * 2;
outer_width = inner_width + wall_thickness * 2;
total_height = base_thickness + wall_height;

strap_width = 26.0;
strap_thickness = 1.3;
strap_slot_length = 30.0;
strap_slot_width = 4.0;
strap_slot_radius = 2.0;
strap_slot_outer_margin = 3.0;
strap_slot_break_extra = 8.0;

mount_hole_diameter = 3.2;
mount_hole_center_offset = 8.0;

eva_length = 133.0;
eva_width = 75.0;
eva_thickness = 2.0;

module rounded_cube(size, r) {
    hull() {
        for (x = [-size[0] / 2 + r, size[0] / 2 - r])
            for (y = [-size[1] / 2 + r, size[1] / 2 - r])
                translate([x, y, 0])
                    cylinder(h = size[2], r = r);
    }
}

module rounded_slot_2d(length, width, radius) {
    hull() {
        translate([-length / 2 + radius, 0, 0])
            circle(r = radius);
        translate([length / 2 - radius, 0, 0])
            circle(r = radius);
    }
}

module strap_slot_cut(x, y) {
    translate([x, y, -0.1])
        linear_extrude(height = base_thickness + 0.2)
            rounded_slot_2d(strap_slot_length, strap_slot_width, strap_slot_radius);
}

module mount_hole_cut(x, y) {
    translate([x, y, -0.1])
        cylinder(h = base_thickness + 0.2, d = mount_hole_diameter);
}

module base_plate() {
    difference() {
        translate([0, 0, base_thickness / 2])
            cube([outer_length, outer_width, base_thickness], center = true);

        for (x = [-outer_length / 2 + mount_hole_center_offset,
                  outer_length / 2 - mount_hole_center_offset])
            for (y = [-outer_width / 2 + mount_hole_center_offset,
                      outer_width / 2 - mount_hole_center_offset])
                mount_hole_cut(x, y);

        for (x = [-inner_length / 4, inner_length / 4])
            for (y = [-outer_width / 2 + strap_slot_outer_margin + strap_slot_width / 2,
                      outer_width / 2 - strap_slot_outer_margin - strap_slot_width / 2])
                strap_slot_cut(x, y);
    }
}

module walls() {
    z = base_thickness + wall_height / 2;

    // Short end walls.
    translate([-inner_length / 2 - wall_thickness / 2, 0, z])
        cube([wall_thickness, outer_width, wall_height], center = true);
    translate([inner_length / 2 + wall_thickness / 2, 0, z])
        cube([wall_thickness, outer_width, wall_height], center = true);

    // Long side walls, split at the two strap positions.
    break_len = strap_slot_length + strap_slot_break_extra;
    side_y = inner_width / 2 + wall_thickness / 2;

    for (side = [-1, 1]) {
        for (seg = [
            [-outer_length / 2, -inner_length / 4 - break_len / 2],
            [-inner_length / 4 + break_len / 2, inner_length / 4 - break_len / 2],
            [inner_length / 4 + break_len / 2, outer_length / 2]
        ]) {
            translate([(seg[0] + seg[1]) / 2, side * side_y, z])
                cube([seg[1] - seg[0], wall_thickness, wall_height], center = true);
        }
    }
}

module power_tray() {
    union() {
        base_plate();
        walls();
    }
}

power_tray();
