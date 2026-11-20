"""Q235B 6 mm MAG decision baseline. Source rows remain reference evidence."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


DATABASE = Path(__file__).resolve().parent.parent / "Q235B_MAG_6mm_参数资料库_V0.3.xlsx"


@dataclass(frozen=True)
class Conditions:
    material: str = "Q235B"
    thickness_mm: float = 6.0
    joint: str = "I形对接"
    position: str = "PA"
    gas: str = "100% CO₂"
    root_gap_mm: float = 1.0


@lru_cache(maxsize=2)
def load_records(path: str = str(DATABASE)) -> tuple[dict[str, Any], ...]:
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = book["参数库"]
        values = sheet.values
        headers = next(values)
        records = tuple(dict(zip(headers, row)) for row in values)
    finally:
        book.close()
    ids = [row["记录ID"] for row in records]
    if len(ids) != len(set(ids)) or len(ids) != 8:
        raise ValueError("参数资料库记录ID重复或记录数异常")
    return records


def _same(a: float, b: float) -> bool:
    return abs(float(a) - float(b)) < 1e-6


def _inside(value: float, lower: float, upper: float) -> bool:
    return float(lower) <= float(value) <= float(upper)


def _result(row: dict[str, Any], label: str, status: str, caveat: str) -> dict[str, Any]:
    return {
        "status": status,
        "label": label,
        "source_id": row["记录ID"],
        "source": row["来源"],
        "source_url": row["来源链接"],
        "source_material": row["母材原文范围"],
        "source_joint": row["接头"],
        "wire_diameter_mm": row["焊丝直径_mm"],
        "groove_angle_deg": row["坡口角度_deg"],
        "current_a": row["参考电流_A"],
        "current_min_a": row["电流下限_A"],
        "current_max_a": row["电流上限_A"],
        "voltage_min_v": row["电压下限_V"],
        "voltage_max_v": row["电压上限_V"],
        "travel_speed_mm_min": row["参考焊速_mm_min"],
        "travel_speed_min_mm_min": row["焊速下限_mm_min"],
        "travel_speed_max_mm_min": row["焊速上限_mm_min"],
        "pass_description": row["道次/角色"],
        "wire_feed_m_min": row["送丝速度_m_min"],
        "gas_flow_min_l_min": row["气体流量下限_L_min"],
        "gas_flow_max_l_min": row["气体流量上限_L_min"],
        "ctwd_mm": row["导电嘴距工件_mm"],
        "quality_note": row["质量结果"],
        "caveat": caveat,
        "training_sample": False,
    }


def recommend(c: Conditions, path: str = str(DATABASE)) -> dict[str, Any]:
    """Retrieve all compatible reference schemes without using wire size as input."""
    rows = load_records(path)
    by_id = {row["记录ID"]: row for row in rows}
    if c.material != "Q235B" or c.position != "PA" or not _same(c.thickness_mm, 6.0):
        return {"status": "out_of_scope", "message": "初版只覆盖Q235B、6 mm、PA平焊。", "matches": []}

    lincoln = by_id["LINCOLN-GMAW-6MM-CO2"]
    otc = by_id["OTC-CO2-6MM-I-2PASS"]
    paper = by_id["JAES-SS400-6MM-500"]
    matches = []
    if c.joint == "I形对接" and c.gas == "100% CO₂":
        if _inside(c.root_gap_mm, 0, 1.6):
            matches.append(_result(
                lincoln, "厂家试焊参考", "reference_match",
                "原文为碳钢短路过渡指南，电流是近似值；道次未明确；Q235B焊透和质量尚未试验确认。"
            ))
        if _inside(c.root_gap_mm, 1.2, 1.5):
            matches.append(_result(
                otc, "厂家双面焊参考", "reference_match",
                "原表为正面和反面各焊一道，共2层；该行未明确标示PA位置，且不是Q235B实测，不能作为单面单道推荐。"
            ))
    if c.joint == "单V形对接" and c.gas == "82% Ar + 18% CO₂" and _same(c.root_gap_mm, 2):
        matches.append(_result(
            paper, "相近材料论文典型案例", "analog_match",
            "原文为SS400、60°坡口、单面单道；500 mm/min仅是论文对照组之一，不是Q235B已验证参数。"
        ))
    if matches:
        return {"status": "reference_matches", "matches": matches}

    nearest = lincoln if c.gas == "100% CO₂" else paper
    return {
        "status": "no_exact_reference",
        "message": "资料库中没有同时匹配板厚、接头、保护气和根部间隙的参考工况。",
        "matches": [],
        "reference": {
            "source_id": nearest["记录ID"],
            "source": nearest["来源"],
            "source_url": nearest["来源链接"],
            "source_material": nearest["母材原文范围"],
            "source_joint": nearest["接头"],
            "source_gas": nearest["保护气"],
            "source_wire_mm": nearest["焊丝直径_mm"],
        },
    }


def standard_context(c: Conditions, path: str = str(DATABASE)) -> dict[str, Any]:
    """Expose GB 50661 conditional ranges without treating them as a universal check."""
    rows = load_records(path)
    national = [row for row in rows if row["数据类别"] == "国标条件范围"]
    return {
        "directly_comparable": False,
        "note": "GB 50661第6.6节是特定条件下的免评定范围；本组尚未核实全部条件，不能将其当作本工况合格判定或单道配方。",
        "ranges": [
            {
                "role": row["道次/角色"], "current_min_a": row["电流下限_A"],
                "current_max_a": row["电流上限_A"], "voltage_min_v": row["电压下限_V"],
                "voltage_max_v": row["电压上限_V"], "speed_min_mm_min": row["焊速下限_mm_min"],
                "speed_max_mm_min": row["焊速上限_mm_min"], "source_url": row["来源链接"],
            } for row in national
        ],
    }
