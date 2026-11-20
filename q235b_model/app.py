import streamlit as st

from model import Conditions, recommend, standard_context


st.set_page_config(page_title="Q235B MAG 工艺决策 V0.1", layout="wide")
st.title("Q235B 6 mm MAG 工艺决策模型 V0.1")
st.caption("基于来源记录的试焊参考；尚未使用本组试件完成工艺验证。")

with st.sidebar:
    st.header("输入工况")
    st.caption("固定条件：Q235B · PA平焊 · I形对接")
    thickness = st.number_input("板厚 (mm)", min_value=1.0, max_value=50.0, value=6.0, step=0.5)
    gas = st.selectbox("保护气", ["100% CO₂", "82% Ar + 18% CO₂"])
    wire = st.number_input("实心焊丝直径 (mm)", min_value=0.6, max_value=2.0, value=1.1, step=0.1)
    gap = st.number_input("根部间隙 (mm)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
    generate = st.button("生成焊接参数", type="primary", use_container_width=True)

c = Conditions(thickness_mm=thickness, gas=gas, wire_diameter_mm=wire, root_gap_mm=gap)
if st.session_state.get("submitted_conditions") not in (None, c):
    del st.session_state["submitted_conditions"]
if generate:
    st.session_state["submitted_conditions"] = c

if st.session_state.get("submitted_conditions") == c:
    result = recommend(c)
    if result["status"] in {"reference_match", "analog_match"}:
        st.subheader(result["label"])
        a, b, v = st.columns(3)
        current = f"约 {result['current_a']} A" if result["current_a"] is not None else f"{result['current_min_a']}–{result['current_max_a']} A"
        a.metric("电流", current)
        voltage = f"{result['voltage_min_v']}–{result['voltage_max_v']} V" if result['voltage_min_v'] != result['voltage_max_v'] else f"{result['voltage_min_v']} V"
        b.metric("电压", voltage)
        speed = str(result["travel_speed_mm_min"]) if result["travel_speed_mm_min"] is not None else f"{result['travel_speed_min_mm_min']}–{result['travel_speed_max_mm_min']}"
        v.metric("焊接速度", f"{speed} mm/min")
        st.write(f"焊接道次：{result['pass_description']}。")
        details = [f"保护气流量：{result['gas_flow_min_l_min']}–{result['gas_flow_max_l_min']} L/min"]
        if result["wire_feed_m_min"] is not None:
            details.append(f"送丝速度：{result['wire_feed_m_min']} m/min")
        if result["ctwd_mm"] is not None:
            details.append(f"导电嘴距工件：{result['ctwd_mm']} mm")
        st.write("；".join(details) + "。")
        st.warning(result["caveat"])
        if result["quality_note"]:
            st.info(result["quality_note"])
        st.markdown(f"来源记录：**{result['source_id']}** · [{result['source']}]({result['source_url']})")
    else:
        st.warning(result["message"])
        if result.get("reference"):
            ref = result["reference"]
            st.write(f"最近参考：{ref['source_id']}；原文母材 {ref['source_material']}，接头 {ref['source_joint']}，保护气 {ref['source_gas']}，焊丝 {ref['source_wire_mm']} mm。")
            st.markdown(f"[查看原始来源]({ref['source_url']})")

    with st.expander("国标范围及适用条件"):
        std = standard_context(c)
        st.write(std["note"])
        st.dataframe([{k:v for k,v in r.items() if k != "source_url"} for r in std["ranges"]], hide_index=True)
        st.markdown(f"[查看 GB 50661—2011 原文]({std['ranges'][0]['source_url']})")
else:
    st.info("请在左侧填写工况，然后点击“生成焊接参数”。")

st.caption("模型类型：规则匹配与来源检索；训练样本 0；不输出预测精度或不确定度。实心焊丝 MAG 的 ISO 4063 代号为 135。")
