import streamlit as st

from model import Conditions, recommend, standard_context


def load_example(joint: str, gas: str, gap: float) -> None:
    st.session_state["thickness"] = 6.0
    st.session_state["joint"] = joint
    st.session_state["gas"] = gas
    st.session_state["gap"] = gap
    st.session_state.pop("submitted_conditions", None)


def show_reference(ref: dict, number: int, total: int) -> None:
    st.subheader(f"方案 {number}：{ref['label']}" if total > 1 else ref["label"])
    st.write(
        f"原文母材：**{ref['source_material']}**；接头：**{ref['source_joint']}**；"
        f"实心焊丝直径：**{ref['wire_diameter_mm']} mm**。"
    )
    if ref["groove_angle_deg"] is not None:
        st.write(f"原文坡口角度：{ref['groove_angle_deg']}°。")
    a, b, v = st.columns(3)
    current = f"约 {ref['current_a']} A" if ref["current_a"] is not None else f"{ref['current_min_a']}–{ref['current_max_a']} A"
    voltage = f"{ref['voltage_min_v']}–{ref['voltage_max_v']} V" if ref["voltage_min_v"] != ref["voltage_max_v"] else f"{ref['voltage_min_v']} V"
    speed = str(ref["travel_speed_mm_min"]) if ref["travel_speed_mm_min"] is not None else f"{ref['travel_speed_min_mm_min']}–{ref['travel_speed_max_mm_min']}"
    a.metric("电流", current)
    b.metric("电压", voltage)
    v.metric("焊接速度", f"{speed} mm/min")
    st.write(f"焊接道次：{ref['pass_description']}。")
    details = [f"保护气流量：{ref['gas_flow_min_l_min']}–{ref['gas_flow_max_l_min']} L/min"]
    if ref["wire_feed_m_min"] is not None:
        details.append(f"送丝速度：{ref['wire_feed_m_min']} m/min")
    if ref["ctwd_mm"] is not None:
        details.append(f"导电嘴距工件：{ref['ctwd_mm']} mm")
    st.write("；".join(details) + "。")
    st.warning(ref["caveat"])
    if ref["quality_note"]:
        st.info(ref["quality_note"])
    st.markdown(f"来源记录：**{ref['source_id']}** · [{ref['source']}]({ref['source_url']})")


st.set_page_config(page_title="Q235B MAG 工艺决策 V0.2", layout="wide")
st.title("Q235B 6 mm MAG 工艺决策模型 V0.2")
st.caption("基于来源记录的试焊参考；尚未使用本组 Q235B 试件完成工艺验证。")

with st.sidebar:
    st.header("输入工况")
    st.caption("固定条件：Q235B · PA 平焊；目前仅有 6 mm 参考。")
    with st.expander("载入典型案例"):
        st.button("I 形，CO₂，间隙 1.0 mm", on_click=load_example, args=("I形对接", "100% CO₂", 1.0), use_container_width=True)
        st.button("I 形，CO₂，间隙 1.3 mm", on_click=load_example, args=("I形对接", "100% CO₂", 1.3), use_container_width=True)
        st.button("单 V 形，Ar/CO₂，间隙 2.0 mm", on_click=load_example, args=("单V形对接", "82% Ar + 18% CO₂", 2.0), use_container_width=True)
    thickness = st.number_input("板厚 (mm)", min_value=1.0, max_value=50.0, value=6.0, step=0.5, key="thickness")
    joint = st.selectbox("接头形式", ["I形对接", "单V形对接"], key="joint")
    gas = st.selectbox("保护气", ["100% CO₂", "82% Ar + 18% CO₂"], key="gas")
    gap = st.number_input("根部间隙 (mm)", min_value=0.0, max_value=10.0, value=1.0, step=0.1, key="gap")
    generate = st.button("生成焊接参数", type="primary", use_container_width=True)

c = Conditions(thickness_mm=thickness, joint=joint, gas=gas, root_gap_mm=gap)
if st.session_state.get("submitted_conditions") not in (None, c):
    st.session_state.pop("submitted_conditions", None)
if generate:
    st.session_state["submitted_conditions"] = c

if st.session_state.get("submitted_conditions") == c:
    result = recommend(c)
    if result["status"] == "reference_matches":
        matches = result["matches"]
        if len(matches) > 1:
            st.info("当前输入匹配多个来源方案。焊丝直径和焊接道次随方案不同，请结合实际试验方案选择。")
        for i, ref in enumerate(matches, 1):
            show_reference(ref, i, len(matches))
            if i < len(matches):
                st.divider()
    else:
        st.warning(result["message"])
        if result.get("reference"):
            ref = result["reference"]
            st.write(f"相近来源仅供查阅：{ref['source_id']}；原文母材 {ref['source_material']}，接头 {ref['source_joint']}，保护气 {ref['source_gas']}，焊丝 {ref['source_wire_mm']} mm。")
            st.markdown(f"[查看原始来源]({ref['source_url']})")

    with st.expander("国标范围及适用条件"):
        std = standard_context(c)
        st.write(std["note"])
        st.dataframe([{k: v for k, v in row.items() if k != "source_url"} for row in std["ranges"]], hide_index=True)
        st.markdown(f"[查看 GB 50661—2011 原文]({std['ranges'][0]['source_url']})")
else:
    st.info("请在左侧填写工况，然后点击“生成焊接参数”。")

st.caption("模型类型：规则匹配与来源检索；Q235B 实测训练样本 0。实心焊丝 MAG 的 ISO 4063 代号为 135。")
