from datetime import datetime
from models.result_models import EquipmentResult


def generate_pdf(result: EquipmentResult, filepath: str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
    except ImportError:
        raise ImportError("reportlab 패키지가 필요합니다: pip install reportlab")

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    styles = getSampleStyleSheet()
    style_title  = ParagraphStyle("title",  fontSize=16, fontName="Helvetica-Bold",
                                   spaceAfter=6, leading=20)
    style_h2     = ParagraphStyle("h2",     fontSize=12, fontName="Helvetica-Bold",
                                   spaceBefore=12, spaceAfter=4, textColor=colors.HexColor("#1565C0"))
    style_normal = ParagraphStyle("normal", fontSize=9,  fontName="Helvetica", leading=14)
    style_small  = ParagraphStyle("small",  fontSize=8,  fontName="Helvetica",
                                   textColor=colors.grey)

    tbl_style = TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1565C0")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("BACKGROUND",   (0, 1), (0, -1), colors.HexColor("#E3F2FD")),
        ("FONTNAME",     (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("ALIGN",        (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ])

    story = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    story.append(Paragraph("사료플랜트 기계 설계 계산서", style_title))
    story.append(Paragraph(f"장비: {result.equipment_type}  |  작성일: {ts}", style_small))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1565C0")))
    story.append(Spacer(1, 8*mm))

    # 모터
    story.append(Paragraph("1. 모터 선정 결과", style_h2))
    m = result.motor
    motor_data = [
        ["항목", "값", "단위"],
        ["필요 동력",     f"{m.required_power_kW:.3f}", "kW"],
        ["선정 모터 용량", f"{m.selected_motor_kW}",    "kW"],
        ["모터 모델",     m.motor_model,                 ""],
        ["IEC 프레임",    m.iec_frame,                   ""],
        ["정격 회전수",   f"{m.rated_rpm}",              "rpm"],
        ["정격 전류(400V)", f"{m.rated_current_A}",      "A"],
        ["정격 토크",     f"{m.rated_torque_Nm}",        "N·m"],
        ["효율",          f"{m.efficiency_pct}",         "%"],
    ]
    t = Table(motor_data, colWidths=[70*mm, 60*mm, 40*mm])
    t.setStyle(tbl_style)
    story.append(t)
    story.append(Spacer(1, 6*mm))

    # 베어링
    story.append(Paragraph("2. 베어링 선정 결과 (ISO 281)", style_h2))
    bd, bdn = result.bearing_drive, result.bearing_driven
    bearing_data = [
        ["항목",                  "구동측",                     "피동측"],
        ["베어링 번호",            bd.bearing_number,            bdn.bearing_number],
        ["제조사",                 bd.manufacturer,              bdn.manufacturer],
        ["내경 (mm)",              f"{bd.bore_mm:.0f}",          f"{bdn.bore_mm:.0f}"],
        ["외경 (mm)",              f"{bd.outer_dia_mm:.0f}",     f"{bdn.outer_dia_mm:.0f}"],
        ["폭 (mm)",                f"{bd.width_mm:.0f}",         f"{bdn.width_mm:.0f}"],
        ["등가하중 P (N)",         f"{bd.equivalent_load_P_N:,.0f}", f"{bdn.equivalent_load_P_N:,.0f}"],
        ["기본동정격하중 C (N)",   f"{bd.basic_load_rating_C_N:,.0f}", f"{bdn.basic_load_rating_C_N:,.0f}"],
        ["L10 수명 (hr)",          f"{bd.L10_hr:,.0f}",          f"{bdn.L10_hr:,.0f}"],
    ]
    t2 = Table(bearing_data, colWidths=[70*mm, 55*mm, 45*mm])
    t2.setStyle(tbl_style)
    story.append(t2)
    story.append(Spacer(1, 6*mm))

    # 샤프트
    story.append(Paragraph("3. 샤프트 설계 결과 (ASME)", style_h2))
    s = result.shaft
    shaft_data = [
        ["항목", "값", "단위"],
        ["재질",          s.material,                    ""],
        ["계산 직경",     f"{s.required_diameter_mm:.2f}", "mm"],
        ["선정 직경(KS)", f"{s.selected_diameter_mm:.0f}", "mm"],
        ["Von Mises 응력", f"{s.von_mises_stress_MPa:.2f}", "MPa"],
        ["허용 응력",     f"{s.allowable_stress_MPa:.2f}", "MPa"],
        ["실제 안전계수", f"{s.safety_factor_actual:.2f}", ""],
    ]
    t3 = Table(shaft_data, colWidths=[70*mm, 60*mm, 40*mm])
    t3.setStyle(tbl_style)
    story.append(t3)
    story.append(Spacer(1, 6*mm))

    # 감속기
    story.append(Paragraph("4. 감속기 선정 결과", style_h2))
    rd = result.reducer
    reducer_data = [
        ["항목", "값", "단위"],
        ["모델",      rd.model,                      ""],
        ["감속비",    f"{rd.ratio:.2f}",              ""],
        ["입력 토크", f"{rd.input_torque_Nm:.1f}",   "N·m"],
        ["출력 토크", f"{rd.output_torque_Nm:.1f}",  "N·m"],
        ["효율",      f"{rd.efficiency_pct}",         "%"],
    ]
    t4 = Table(reducer_data, colWidths=[70*mm, 60*mm, 40*mm])
    t4.setStyle(tbl_style)
    story.append(t4)
    story.append(Spacer(1, 6*mm))

    # V벨트
    story.append(Paragraph("5. V벨트 선정 결과 (KS B 1400)", style_h2))
    vb = result.vbelt
    vbelt_data = [
        ["항목", "값", "단위"],
        ["단면",           vb.section,                       ""],
        ["호칭",           vb.belt_length_designation,       ""],
        ["벨트 길이",      f"{vb.belt_length_mm:.0f}",       "mm"],
        ["벨트 수량",      f"{vb.number_of_belts}",          "개"],
        ["구동 풀리 직경", f"{vb.drive_pulley_dia_mm:.0f}",  "mm"],
        ["피동 풀리 직경", f"{vb.driven_pulley_dia_mm:.0f}", "mm"],
        ["실제 감속비",    f"{vb.actual_ratio:.3f}",          ""],
        ["접촉각",         f"{vb.contact_angle_deg:.1f}",    "°"],
    ]
    t5 = Table(vbelt_data, colWidths=[70*mm, 60*mm, 40*mm])
    t5.setStyle(tbl_style)
    story.append(t5)

    if result.calculation_notes:
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph("6. 계산 메모 및 경고", style_h2))
        for note in result.calculation_notes:
            story.append(Paragraph(note, style_normal))

    doc.build(story)
