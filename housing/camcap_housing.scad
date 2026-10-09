// CamCap housing - v0.5, OpenSCAD
//
// v0.5.2: the corner of the mounting plate in front of the power slot is
// cut away. As printed it hung over the slot with nothing under it.
//
// v0.5.1: the back-right corner is left square behind the strap loops, so
// the loops no longer overhang the chamfer there.
//
// v0.5: the bezel window is bevelled; the edges around the fan wall are
// chamfered to match the long edges; the nut slot has crush ribs so the nut
// stays put; the fan holes take Noctua's rubber anti-vibration mounts
// instead of screws (print part = "fan_mount_test" first to check the fit).
//
// v0.4: the four long outside edges of the body, and the matching corners
// of the bezel, are chamfered.
// The screw tabs moved 2mm toward the middle so each chamfer turns into a
// short straight edge and meets its tab at a right angle.
//
// v0.3: the built-in cold-shoe foot is replaced by a plate on the bottom
// that screws onto a ball-head shoe mount (1/4"-20 captive nut, plus a slot
// for the mount's anti-twist pin). The power slot is 1" longer to the right,
// and the display stops stick out 1mm further from each side wall.
//
// v0.2: display and Pi dimensions taken from the official drawings
// (RP-010430-MM-1 Touch Display 2 5" product brief, RP-008343-DS-1 Pi 4
// mechanical drawing). The display is now held by its cover glass, which is
// the only part that fills the full 143.4 x 91.46 outline.
//
// An upright, field-monitor style case that sits on a ball-head shoe mount
// on the FX7's accessory shoe:
//   - the 5" Touch Display 2 faces the operator (toward the back of the camera)
//   - the Pi 4 mounts on the back of the display, components facing forward
//   - a 40mm Noctua fan on the camera-facing wall blows straight onto the Pi's
//     SoC; hot air leaves through the slots in the top
//   - the Cam Link and SSD enclosure attach to loops on the right side with
//     velcro straps
//
// Two printed parts: the body (a 5-sided box, open at the back) and the bezel
// (a frame that holds the display in the body with 4x M3x12 screws that
// self-tap into the ears).
//
// Check the one line marked CHECK against the real parts before printing.
//
// Mounting plate: drop a 1/4"-20 hex nut into the slot in the plate's back
// face (camera side) and screw the ball-head mount up into it.
//
// Coordinates: x = left/right as the operator sees it, y = depth (y = 0 is
// the display face, +y points toward the front of the camera), z = up.
//
// Printing: "body" comes out front-wall-down, "bezel" face-down. Every
// overhang in the body is 45 degrees or bridged, so no supports are needed.

// Which part to render: "all" (exploded view), "body", "bezel",
// "fan_mount_test"
part = "all";

// ---- Display (Touch Display 2, 5", used landscape) ----
// From the RP-010430-MM-1 drawing (drawn portrait; width/height swapped here).
disp_w  = 143.4;  // cover glass outline
disp_h  = 91.46;
lens_t  = 0.7;    // cover glass thickness
view_w  = 111.4;  // visible area
view_h  = 63.1;
view_dx = 0;      // the drawing doesn't dimension the window's position;
view_dz = 0;      //   it scales as centred to within ~0.3mm
// Everything behind the glass is smaller than it: the LCD module is inset
// ~5mm from the long edges, and the back plate 9.25mm (sides), 7.86mm (top
// end) and 12.8mm (ribbon cable end). The display stops touch the glass
// within 3mm of its edge, so they clear all of it.
pi_face_y = 14.92;  // glass front to the tips of the Pi standoffs (= Pi underside)

// Glass stands this far proud of the body front, so the bezel clamps it
// instead of leaving it loose.
glass_proud = 0.2;

// ---- Pi 4 (RP-008343-DS-1) ----
// The Pi sits on the display's standoffs with components facing the camera,
// USB/Ethernet end pointing left (as the operator sees it). The standoffs
// are 49 x 58mm, centred across the display's height, with the nearer row
// 33.91mm from the display's ribbon-cable end.
pi_len = 85;
pi_wid = 56;
pi_t   = 1.5;
pi_tallest = 16;     // USB stack height above the board
// Left edge of the display to the Pi's USB/Ethernet board edge. This is
// 33.91 - 23.5 = 10.41 with the ribbon-cable end of the display on the
// left, which matches the touch calibration in system/99-camcap-touch.rules.
// CHECK against the real parts: if the Pi's ports end up ~28mm from the
// edge, the Pi is mounted the other way round.
pi_usb_edge_x = 10.41;
pi_centre_z   = 0;   // standoffs are centred across the display

// Points on the Pi, from the drawing: x from the SD card end, z up from
// the edge with the USB-C/HDMI/audio connectors.
soc_px = 25.75;   soc_pz = 32.5;
usbc_px = 11.2;   // USB-C power socket centre

// ---- Fan (Noctua NF-A4x10 5V PWM) ----
fan_size         = 40;
fan_t            = 10;
fan_hole_spacing = 32;
fan_gap          = 3;   // between the top of the USB stack and the fan
// Rubber anti-vibration mounts (NA-AV3, in the fan's box). Noctua doesn't
// publish the hole size or panel thickness, so these are typical case-fan
// values: check with the fan_mount_test piece and adjust before printing
// the body.
av_hole  = 5;     // hole the rubber mount pulls through
av_panel = 1.2;   // wall is thinned to this around each hole (from inside)
av_spot  = 8;     // diameter of the thinned area

// ---- Derived Pi positions, relative to the display centre ----
// The Pi's SD card end is on the right, so a point px along the board sits
// at pi_usb_edge_x + (pi_len - px) from the display's left edge.
function pi_x(px) = pi_usb_edge_x + (pi_len - px) - disp_w/2;
fan_dx   = pi_x(soc_px);                  // fan centred over the SoC
fan_dz   = pi_centre_z + soc_pz - pi_wid/2;
power_dx = pi_x(usbc_px);                 // power slot under the USB-C socket

// ---- Mounting plate (for a ball-head shoe mount, 1/4"-20 screw) ----
plate_w    = 44;     // across x; runs the full depth of the body
nut_af     = 11.11;  // 1/4"-20 hex nut, 7/16" across flats
nut_t      = 5.56;   //   and 7/32" thick
nut_clear  = 0.3;    // so the nut slides into its slot
plate_skin = 1.5;    // plastic under the nut; the mount's screw must reach
                     //   past this into the nut (these screws are often ~6mm)
plate_t    = plate_skin + nut_t + nut_clear;
screw_d    = 6.8;    // 1/4" clearance
screw_y    = 33;     // behind the power slot, so the nut slot misses it
// Anti-twist pin: a slot running left from the screw, so it catches pins at
// any offset from 9 to 16mm.
pin_w      = 4.5;
pin_r0     = 9;
pin_r1     = 16;
rib_h      = 0.3;    // crush ribs in the nut slot: 0.15mm interference a side

// ---- General ----
wall    = 2.5;
corner  = 3;     // 45-degree chamfer on the outside corners; keep it under
                 //   2 x wall, it leaves (2*wall - corner)/sqrt(2) at the corner
clear   = 0.5;   // gap around the display
bezel_t = 2.5;
window_bevel = bezel_t - 0.5;
m3      = 3.4;   // M3 clearance hole
m3_tap  = 2.8;   // pilot hole for an M3 screw to self-tap into

$fn = 48;

// ---- Derived ----
in_w = disp_w + 2*clear;
in_h = disp_h + 2*clear;
ow = in_w + 2*wall;                           // outside width
oh = in_h + 2*wall;                           // outside height
stop_y = lens_t - glass_proud;                // back of the glass seats against the stops here
pcb_y  = pi_face_y - glass_proud;             // underside of the Pi
fan_y  = pcb_y + pi_t + pi_tallest + fan_gap; // Pi-facing side of the fan
od = fan_y + fan_t + wall;                    // outside depth
ear_z = [10, oh - 10];                        // screw tabs; leaves a 2mm straight edge past the corner chamfer

// ------------------------------------------------------------------ body ---

module body() {
    difference() {
        union() {
            difference() {
                cube([ow, od, oh]);
                translate([wall, -1, wall]) cube([in_w, od - wall + 1, in_h]);
            }
            display_stops();
            for (z = ear_z) {
                translate([0, 0, z - 5]) mirror([1, 0, 0]) ear();
                translate([ow, 0, z - 5]) ear();
            }
            strap_loops();
            mount_plate();
        }
        corner_chamfers(-1, od + 2);
        back_chamfers();
        fan_cutout();
        top_vents();
        usb_window();
        power_slot();
        mount_plate_cuts();
    }
}

// Ribs down each side wall that the display is pushed against. The front
// face is chamfered 45 degrees so they print without supports.
stop_w = 3.5;
module display_stops() {
    hull() {
        translate([wall, stop_y, wall]) cube([stop_w, 2, in_h]);
        translate([wall, stop_y + 2 + stop_w, wall]) cube([0.01, 0.01, in_h]);
    }
    hull() {
        translate([ow - wall - stop_w, stop_y, wall]) cube([stop_w, 2, in_h]);
        translate([ow - wall - 0.01, stop_y + 2 + stop_w, wall]) cube([0.01, 0.01, in_h]);
    }
}

// Screw ear for the bezel, attached at x = 0 and sticking out along +x.
module ear() {
    difference() {
        hull() {
            cube([8, 8, 10]);
            translate([0, 16, 0]) cube([0.01, 0.01, 10]);
        }
        translate([4, -1, 5]) rotate([-90, 0, 0]) cylinder(d = m3_tap, h = 11);
    }
}

// Two loops on the right wall for velcro straps (Cam Link, SSD enclosure).
loop_z = [oh*0.3, oh*0.7];   // loop centres; each loop is 26mm tall
module strap_loops() {
    for (z = loop_z)
        translate([ow, od/2 - 4, z - 13])
            difference() {
                cube([5, od/2 + 4, 26]);
                translate([-1, -1, 2]) cube([4, od, 22]);
            }
}

// Plate under the floor, centred across the body, full depth.
module mount_plate() {
    translate([ow/2 - plate_w/2, 0, -plate_t]) cube([plate_w, od, plate_t + 0.01]);
}

module mount_plate_cuts() {
    // Corner of the plate between the power slot and the display end: it
    // would print hanging over the slot, so it's removed (plate only, not
    // the floor)
    translate([ow/2 + power_dx - 8, -1, -plate_t - 1])
        cube([plate_w, pcb_y + 10 + 1, plate_t + 1]);
    // Screw hole, through the plate and the floor so a long screw can't bottom out
    translate([ow/2, screw_y, -plate_t - 1]) cylinder(d = screw_d, h = plate_t + wall + 2);
    // Nut slot: the nut slides in from the back face, flats along the slot
    // Crush ribs down each side of the slot grip the nut so it can't fall out
    // while the mount is off; they shave down as the nut is pushed in.
    w = nut_af + nut_clear;
    difference() {
        union() {
            translate([ow/2, screw_y, -plate_t + plate_skin])
                rotate([0, 0, 30]) cylinder(d = w / cos(30), h = nut_t + nut_clear, $fn = 6);
            translate([ow/2 - w/2, screw_y, -plate_t + plate_skin])
                cube([w, od - screw_y + 1, nut_t + nut_clear]);
        }
        for (sx = [-1, 1])
            translate([ow/2 + sx*(w/2 - rib_h/2) - rib_h/2, screw_y - 3,
                       -plate_t + plate_skin + (nut_t + nut_clear)/2 - 0.5])
                cube([rib_h, od - screw_y + 4, 1]);
    }
    // Anti-twist pin slot, to the left (away from the power slot)
    hull()
        for (r = [pin_r0, pin_r1])
            translate([ow/2 - r, screw_y, -plate_t - 1]) cylinder(d = pin_w, h = plate_t + 1);
}

module fan_cutout() {
    cx = ow/2 + fan_dx;
    cz = oh/2 + fan_dz;
    // Round opening with three bars left across it as a finger guard
    difference() {
        translate([cx, od - wall - 1, cz]) rotate([-90, 0, 0])
            cylinder(d = fan_size - 3, h = wall + 2);
        for (i = [-1, 0, 1])
            translate([cx - fan_size/2, od - wall - 2, cz + i*10 - 1])
                cube([fan_size, wall + 4, 2]);
    }
    for (sx = [-1, 1], sz = [-1, 1])
        translate([cx + sx*fan_hole_spacing/2, od - wall - 1, cz + sz*fan_hole_spacing/2])
            rotate([-90, 0, 0]) av_hole_cut();
}

// One rubber-mount hole, starting 1mm inside the wall's inner face (local
// z = 0) and going out through the wall.
module av_hole_cut() {
    cylinder(d = av_hole, h = wall + 2);
    cylinder(d = av_spot, h = 1 + wall - av_panel);
}

module top_vents() {
    n = 13;
    pitch = 7;
    for (i = [0 : n - 1])
        translate([ow/2 - (n - 1)*pitch/2 + i*pitch - 1.5, 10, oh - wall - 1])
            cube([3, od - 20, wall + 2]);
}

// Left wall: opening for the Pi's USB/Ethernet end.
module usb_window() {
    translate([-1, pcb_y - 1, oh/2 + pi_centre_z - 28])
        cube([wall + 2, 20, 56]);
}

// Bottom wall: slot for the USB-C power plug/cable. Starts under the USB-C
// socket and runs 1" to the right of the original 16mm slot. Also cut
// through the mounting plate where they overlap.
power_slot_len = 16 + 25.4;
module power_slot() {
    translate([ow/2 + power_dx - 8, pcb_y - 2, -plate_t - 1])
        cube([power_slot_len, 12, plate_t + wall + 2]);
}

// Cuts the four corners of the ow x oh outline at 45 degrees, from y0 for len.
module corner_chamfers(y0, len) {
    for (c = [[0, 0, 0], [ow, 0, 90], [ow, oh, 180], [0, oh, 270]])
        translate([c[0], y0 + len, c[1]]) rotate([90, 0, 0])
            linear_extrude(len) rotate(c[2])
                polygon([[-1, -1], [corner + 1, -1], [-1, corner + 1]]);
}

// Chamfers the four edges around the fan wall (y = od) to match. The bottom
// edge stops at the mounting plate, and the right edge is left square behind
// each strap loop so the loop has solid wall all the way to its end.
module back_chamfers() {
    // top and bottom edges: triangles in (y, z), extruded along x
    rotate([90, 0, 90]) translate([0, 0, -1]) linear_extrude(ow + 2)
        polygon([[od - corner - 1, oh + 1], [od + 1, oh + 1], [od + 1, oh - corner - 1]]);
    for (x = [[-1, ow/2 - plate_w/2], [ow/2 + plate_w/2, ow + 1]])
        rotate([90, 0, 90]) translate([0, 0, x[0]]) linear_extrude(x[1] - x[0])
            polygon([[od - corner - 1, -1], [od + 1, -1], [od + 1, corner + 1]]);
    // left and right edges: triangles in (x, y), extruded along z
    translate([0, 0, -1]) linear_extrude(oh + 2)
        polygon([[-1, od - corner - 1], [-1, od + 1], [corner + 1, od + 1]]);
    for (z = [[-1, loop_z[0] - 13], [loop_z[0] + 13, loop_z[1] - 13], [loop_z[1] + 13, oh + 1]])
        translate([0, 0, z[0]]) linear_extrude(z[1] - z[0])
            polygon([[ow + 1, od - corner - 1], [ow + 1, od + 1], [ow - corner - 1, od + 1]]);
}

// ----------------------------------------------------------------- bezel ---

module bezel() {
    difference() {
        union() {
            translate([0, -bezel_t, 0]) cube([ow, bezel_t, oh]);
            for (z = ear_z) {
                translate([-8, -bezel_t, z - 5]) cube([8, bezel_t, 10]);
                translate([ow, -bezel_t, z - 5]) cube([8, bezel_t, 10]);
            }
        }
        // Window 1mm larger than the visible area on each side at the glass,
        // bevelled 45 degrees out to the front face (a 0.5mm straight land
        // is left against the glass)
        hull() {
            translate([ow/2 + view_dx - view_w/2 - 1, -0.5, oh/2 + view_dz - view_h/2 - 1])
                cube([view_w + 2, 1.5, view_h + 2]);
            translate([ow/2 + view_dx - view_w/2 - 1 - window_bevel, -bezel_t - 1,
                       oh/2 + view_dz - view_h/2 - 1 - window_bevel])
                cube([view_w + 2 + 2*window_bevel, 1, view_h + 2 + 2*window_bevel]);
        }
        for (z = ear_z, x = [-4, ow + 4])
            translate([x, -bezel_t - 1, z]) rotate([-90, 0, 0])
                cylinder(d = m3, h = bezel_t + 2);
        corner_chamfers(-bezel_t - 1, bezel_t + 2);
    }
}

// ------------------------------------------------------- fan mount test ---

// A strip of fan wall with one mount hole at the current size and one 0.5mm
// either side, to check the rubber mounts pull through and grip.
module fan_mount_test() {
    difference() {
        cube([42, 14, wall]);
        for (i = [0 : 2])
            translate([7 + i*14, 7, -1]) {
                cylinder(d = av_hole - 0.5 + i*0.5, h = wall + 2);
                cylinder(d = av_spot, h = 1 + wall - av_panel);
            }
    }
}

// ---------------------------------------------------------------- output ---

if (part == "body")
    translate([0, 0, od]) rotate([-90, 0, 0]) body();
else if (part == "bezel")
    translate([0, 0, bezel_t]) rotate([90, 0, 0]) bezel();
else if (part == "fan_mount_test")
    fan_mount_test();
else {
    body();
    translate([0, -30, 0]) bezel();
}
