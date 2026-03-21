# ============================================================
# services/ticket_generator.py — PDF Ticket & Boarding Pass
# ============================================================

import os
import random
import string
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from models.flight import Booking


class TicketGenerator:
    """Generates PDF flight tickets and boarding passes."""

    COLORS = {
        "navy":    colors.HexColor("#1a237e"),
        "blue":    colors.HexColor("#1565c0"),
        "light":   colors.HexColor("#e3f2fd"),
        "accent":  colors.HexColor("#ff6f00"),
        "green":   colors.HexColor("#2e7d32"),
        "border":  colors.HexColor("#90a4ae"),
        "text":    colors.HexColor("#1a1a2e"),
        "muted":   colors.HexColor("#546e7a"),
        "white":   colors.white,
    }

    def generate_ticket(self, booking: Booking, output_dir: str = "tickets") -> str:
        """Generate PDF flight ticket."""
        os.makedirs(output_dir, exist_ok=True)
        path = f"{output_dir}/ticket_{booking.pnr}.pdf"

        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        styles = self._styles()
        story  = []
        C      = self.COLORS

        # Header
        story.extend(self._header(booking, styles))

        # Booking ref box
        story.extend(self._booking_ref(booking, styles))

        # Flight details for each segment
        for seg in booking.flight.segments:
            story.extend(self._flight_segment(seg, styles))

        # Passenger details
        story.extend(self._passengers(booking, styles))

        # Fare breakdown
        story.extend(self._fare_breakdown(booking, styles))

        # Important info
        story.extend(self._important_info(booking, styles))

        # Footer
        story.extend(self._footer(styles))

        doc.build(story)
        return path

    def _styles(self):
        C = self.COLORS
        return {
            "title":    ParagraphStyle("t1", fontSize=20, fontName="Helvetica-Bold",
                                        textColor=C["white"], alignment=TA_CENTER),
            "sub":      ParagraphStyle("t2", fontSize=10, fontName="Helvetica",
                                        textColor=C["white"], alignment=TA_CENTER),
            "section":  ParagraphStyle("sec", fontSize=12, fontName="Helvetica-Bold",
                                        textColor=C["navy"], spaceBefore=10, spaceAfter=4),
            "body":     ParagraphStyle("body", fontSize=9.5, fontName="Helvetica",
                                        textColor=C["text"], leading=13),
            "bold":     ParagraphStyle("bold", fontSize=9.5, fontName="Helvetica-Bold",
                                        textColor=C["text"]),
            "muted":    ParagraphStyle("muted", fontSize=8.5, fontName="Helvetica",
                                        textColor=C["muted"]),
            "big":      ParagraphStyle("big", fontSize=28, fontName="Helvetica-Bold",
                                        textColor=C["navy"], alignment=TA_CENTER),
            "center":   ParagraphStyle("ctr", fontSize=10, fontName="Helvetica",
                                        alignment=TA_CENTER),
            "footer":   ParagraphStyle("ftr", fontSize=7.5, fontName="Helvetica",
                                        textColor=C["muted"], alignment=TA_CENTER),
        }

    def _hr(self, color=None):
        return HRFlowable(width="100%", thickness=1,
                          color=color or self.COLORS["border"],
                          spaceAfter=6, spaceBefore=4)

    def _header(self, booking: Booking, styles: dict):
        C = self.COLORS
        seg = booking.flight.segments[0]
        header_data = [[
            Paragraph("✈  SkyAssist", styles["title"]),
            Paragraph(f"FLIGHT TICKET\n{seg.cabin_class.value.upper()} CLASS", styles["sub"]),
        ]]
        t = Table(header_data, colWidths=[10*cm, 7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), C["navy"]),
            ("TOPPADDING", (0,0), (-1,-1), 14),
            ("BOTTOMPADDING",(0,0),(-1,-1), 14),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("RIGHTPADDING",(0,0), (-1,-1), 10),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ]))
        return [t, Spacer(1, 10)]

    def _booking_ref(self, booking: Booking, styles: dict):
        C = self.COLORS
        dep  = booking.flight.departure_time
        data = [
            [Paragraph("BOOKING REFERENCE", styles["muted"]),
             Paragraph("STATUS"),
             Paragraph("DATE BOOKED")],
            [Paragraph(booking.pnr, ParagraphStyle("pnr", fontSize=22,
                        fontName="Helvetica-Bold", textColor=C["accent"])),
             Paragraph(f"✅ {booking.status.value}",
                       ParagraphStyle("st", fontSize=11, fontName="Helvetica-Bold",
                                       textColor=C["green"])),
             Paragraph(booking.booked_at.strftime("%d %b %Y"),
                       ParagraphStyle("dt", fontSize=11, fontName="Helvetica",
                                       textColor=C["text"]))],
        ]
        t = Table(data, colWidths=[6*cm, 5*cm, 6*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), C["light"]),
            ("TOPPADDING",   (0,0), (-1,-1), 8),
            ("BOTTOMPADDING",(0,0), (-1,-1), 8),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ("GRID",         (0,0), (-1,-1), 0.5, C["border"]),
        ]))
        return [t, Spacer(1, 12)]

    def _flight_segment(self, seg, styles: dict):
        C   = self.COLORS
        items = [
            Paragraph(
                f"✈  {seg.flight_number}  ·  {seg.airline_name}  ·  {seg.aircraft_type}",
                styles["section"]
            ),
            self._hr(C["blue"]),
        ]

        dep_str = seg.departure_time.strftime("%H:%M")
        arr_str = seg.arrival_time.strftime("%H:%M")
        dur_h, dur_m = divmod(seg.duration_mins, 60)

        route_data = [[
            Paragraph(seg.origin,  ParagraphStyle("code", fontSize=32,
                       fontName="Helvetica-Bold", textColor=C["navy"],
                       alignment=TA_CENTER)),
            Paragraph(f"──── {dur_h}h {dur_m}m ────\n✈",
                      ParagraphStyle("arr", fontSize=11, fontName="Helvetica",
                                      textColor=C["muted"], alignment=TA_CENTER)),
            Paragraph(seg.destination, ParagraphStyle("code2", fontSize=32,
                       fontName="Helvetica-Bold", textColor=C["navy"],
                       alignment=TA_CENTER)),
        ]]
        rt = Table(route_data, colWidths=[5*cm, 7*cm, 5*cm])
        rt.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
        ]))
        items.append(rt)

        time_data = [[
            Paragraph(dep_str,
                      ParagraphStyle("t", fontSize=20, fontName="Helvetica-Bold",
                                      textColor=C["text"], alignment=TA_CENTER)),
            Paragraph(""),
            Paragraph(arr_str,
                      ParagraphStyle("t", fontSize=20, fontName="Helvetica-Bold",
                                      textColor=C["text"], alignment=TA_CENTER)),
        ]]
        tt = Table(time_data, colWidths=[5*cm, 7*cm, 5*cm])
        tt.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                                ("TOPPADDING",(0,0),(-1,-1),0)]))
        items.append(tt)

        date_data = [[
            Paragraph(seg.departure_time.strftime("%a, %d %b %Y"),
                      ParagraphStyle("d", fontSize=10, fontName="Helvetica",
                                      textColor=C["muted"], alignment=TA_CENTER)),
            Paragraph(""),
            Paragraph(seg.arrival_time.strftime("%a, %d %b %Y"),
                      ParagraphStyle("d", fontSize=10, fontName="Helvetica",
                                      textColor=C["muted"], alignment=TA_CENTER)),
        ]]
        dt = Table(date_data, colWidths=[5*cm, 7*cm, 5*cm])
        dt.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        items.append(dt)
        items.append(Spacer(1, 8))

        info_rows = [
            ["Terminal (Dep)", seg.terminal_dep or "TBA",
             "Terminal (Arr)", seg.terminal_arr or "TBA"],
            ["Check-in Opens",  "48h before departure",
             "Boarding",        "45 min before departure"],
            ["Meal",            "Included" if seg.meal_included else "Not included",
             "Wi-Fi",           "Available" if seg.wifi_available else "Not available"],
        ]
        it = Table(info_rows, colWidths=[3.5*cm, 4.5*cm, 3.5*cm, 5.5*cm])
        it.setStyle(TableStyle([
            ("FONTNAME",     (0,0), (-1,-1), "Helvetica"),
            ("FONTNAME",     (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",     (2,0), (2,-1), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 9),
            ("GRID",         (0,0), (-1,-1), 0.5, C["border"]),
            ("BACKGROUND",   (0,0), (0,-1), C["light"]),
            ("BACKGROUND",   (2,0), (2,-1), C["light"]),
            ("TOPPADDING",   (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0), (-1,-1), 5),
            ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ]))
        items.append(it)
        items.append(Spacer(1, 10))
        return items

    def _passengers(self, booking: Booking, styles: dict):
        C     = self.COLORS
        items = [Paragraph("👤  PASSENGER DETAILS", styles["section"]),
                 self._hr(C["blue"])]

        rows  = [["#", "Passenger Name", "Seat", "Passport", "Meal"]]
        for i, (pax, seat) in enumerate(zip(booking.passengers, booking.seat_numbers), 1):
            rows.append([
                str(i),
                f"{pax.first_name} {pax.last_name}",
                seat,
                pax.passport or "N/A",
                booking.meal_preference,
            ])
        t = Table(rows, colWidths=[0.8*cm, 5.5*cm, 2*cm, 4*cm, 4.7*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), C["blue"]),
            ("TEXTCOLOR",     (0,0), (-1,0), C["white"]),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("GRID",          (0,0), (-1,-1), 0.5, C["border"]),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [C["white"], C["light"]]),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ]))
        items += [t, Spacer(1, 10)]
        return items

    def _fare_breakdown(self, booking: Booking, styles: dict):
        C     = self.COLORS
        fl    = booking.flight
        n     = len(booking.passengers)
        items = [Paragraph("💰  FARE BREAKDOWN", styles["section"]),
                 self._hr(C["blue"])]

        rows  = [
            ["Base Fare (×passengers)", f"₹{fl.price_inr:,.0f} × {n}", f"₹{fl.price_inr*n:,.0f}"],
            ["Taxes & Fees",            "",                              f"₹{fl.taxes_inr*n:,.0f}"],
        ]
        if booking.extra_baggage:
            rows.append(["Extra Baggage", "", f"₹{500*n:,.0f}"])
        if booking.discount_inr:
            rows.append([f"Coupon ({booking.coupon_applied})", "Discount",
                         f"-₹{booking.discount_inr:,.0f}"])
        rows.append(["TOTAL PAID", "", f"₹{booking.total_paid:,.0f}"])

        t = Table(rows, colWidths=[8*cm, 4*cm, 5*cm])
        t.setStyle(TableStyle([
            ("FONTNAME",      (0,-1), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),  (-1,-1), 9.5),
            ("GRID",          (0,0),  (-1,-1), 0.5, C["border"]),
            ("BACKGROUND",    (0,-1), (-1,-1), C["navy"]),
            ("TEXTCOLOR",     (0,-1), (-1,-1), C["white"]),
            ("ROWBACKGROUNDS",(0,0),  (-1,-2), [C["white"], C["light"]]),
            ("TOPPADDING",    (0,0),  (-1,-1), 6),
            ("BOTTOMPADDING", (0,0),  (-1,-1), 6),
            ("LEFTPADDING",   (0,0),  (-1,-1), 8),
        ]))
        items += [t, Spacer(1, 10)]
        return items

    def _important_info(self, booking: Booking, styles: dict):
        C     = self.COLORS
        fl    = booking.flight
        items = [Paragraph("ℹ️  IMPORTANT INFORMATION", styles["section"]),
                 self._hr(C["blue"])]

        info = [
            f"📋 Cabin Baggage: {fl.baggage_cabin}  |  Checked Baggage: {fl.baggage_checked}",
            f"⏰ Check-in opens 48 hours before departure. Online check-in available.",
            f"🔴 Cancellation: {'Refundable' if fl.refundable else 'Non-refundable'}",
        ]
        if booking.cancellation_deadline:
            info.append(f"⏱ Free cancellation until: {booking.cancellation_deadline.strftime('%d %b %Y %H:%M')}")
        info.append("🪪 Carry a valid photo ID / passport to the airport.")
        info.append("✈ Arrive at airport at least 2 hours before departure (3h for international).")

        for line in info:
            items.append(Paragraph(f"• {line}", styles["body"]))
        return items

    def _footer(self, styles: dict):
        return [
            Spacer(1, 14),
            HRFlowable(width="100%", thickness=1, color=self.COLORS["navy"]),
            Paragraph(
                f"Generated by SkyAssist AI · {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
                "For support: support@skyassist.ai · +91-1800-SKY-HELP",
                styles["footer"]
            ),
        ]
