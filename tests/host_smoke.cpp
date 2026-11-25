// C++98 host-only smoke checks. Reads CDS structs; no car or network required.
#include <math.h>
#include <stdio.h>
#include "src/cds_values.hpp"
#include "src/gauge_view.hpp"
int main() {
    eng::Settings s;
    if (s.power != eng::kHp || s.fuel != eng::kGallon) return 1;
    if (fabs(eng::showPower(s, 100.) - 98.632) > .01) return 2;
    if (fabs(eng::showFuel(s, 57.) - (57. / 3.785411784)) > .01) return 3;
    if (eng::powerScaleMin(s) != 300 || eng::torqueScaleMin(s) != 350) return 4;
    eng::Metrics m; eng::Maxima mx; unsigned out[eng::ids::kSlotCount];
    m.hasRpm = true; m.rpm = 2450;
    m.hasSpeed = true; m.speed = 100; // CDS km/h, expected displayed mph = 62
    m.hasTorque = true; m.torque = -51;
    eng::computeView(m,mx,s,out);
    if (out[eng::ids::kSlotRpmBig0] != eng::bigGlyph('2',0)) return 5;
    if (out[eng::ids::kSlotRpmBig1] != eng::bigGlyph('4',0)) return 6;
    if (out[eng::ids::kSlotRpmBig2] != eng::bigGlyph('5',0)) return 7;
    if (out[eng::ids::kSlotRpmBig3] != eng::bigGlyph('0',0)) return 8;
    if (out[eng::ids::kSlotSpeedBig1] != eng::bigGlyph('6',0)) return 9;
    if (out[eng::ids::kSlotSpeedBig2] != eng::bigGlyph('2',0)) return 10;
    if (out[eng::ids::kSlotTorqueBig0] != eng::bigGlyph('-',0)) return 11;
    if (out[eng::ids::kSlotTorqueArc] != eng::ids::kImgArc || m.power() != 0) return 12;
    m.hasRpm = false; m.hasSpeed = false;
    eng::computeView(m,mx,s,out);
    if (out[eng::ids::kSlotRpmBig0] != eng::ids::kImgBlank || out[eng::ids::kSlotSpeedBig2] != eng::ids::kImgBlank) return 13;
    puts("PASS: merged 300 HP / 350 Nm, US gal, signed torque, live RPM & MPH, absent-data blanks");
    return 0;
}
