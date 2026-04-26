import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="校园公交智能调度系统", layout="centered")

st.title("🚌 校园公交智能调度与满载率分析系统")
st.markdown("本系统可自动解析客流调查表，寻找**最大断面客流量**，并实时模拟不同发车间隔下的**满载率与运营成本**。")

# ==========================================
# 模块一：数据导入与最大断面计算
# ==========================================
st.header("第一步：导入客流数据")
st.info("请将你的 Excel 数据（仅限一趟车或一时段的：站点、上车总数、下车总数，共3列）直接粘贴在下方：")

# 默认填入你晚高峰的真实汇总数据作为演示
default_data = """站点	上车人数	下车人数
东体育馆	7	0
融园东	19	3
第三食堂	11	10
秀园	9	3
第二食堂	13	5
综合楼	12	3
一食堂	11	2
西门	7	6
纺化楼	9	1
11号教学楼	10	3
1号教学楼	12	2
逸夫楼	8	4
理科楼	5	4
东操场	9	1
东体育馆	0	9"""

raw_text = st.text_area("在这里粘贴数据（用Tab或逗号分隔均可）：", value=default_data, height=150)

# 解析数据并计算
if raw_text:
    try:
        # 将文本转为 DataFrame
        df = pd.read_csv(io.StringIO(raw_text), sep=None, engine='python')

        # 统一列名以防报错
        df.columns = ["站点", "上车", "下车"]

        # 核心算法：计算断面客流 = 累计上车 - 累计下车
        df['断面客流'] = (df['上车'] - df['下车']).cumsum()

        # 找出最大断面
        max_flow = df['断面客流'].max()
        max_row = df[df['断面客流'] == max_flow].iloc[0]
        max_station = max_row['站点']

        st.success(f"✅ 数据解析成功！全线最大断面出现在 **{max_station}** 驶出后，最大断面客流量为： **{max_flow} 人**。")

        with st.expander("点击查看完整断面客流计算表"):
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("数据格式有误，请确保只有3列：站点名、上车人数、下车人数。")
        max_flow = 19  # 默认值容错

st.divider()

# ==========================================
# 模块二：动态调度与满载率模拟
# ==========================================
st.header("第二步：运力调度模拟器")

# 将统计时段的最大断面客流，按比例换算为“高峰小时”断面客流 (假设刚才的数据是 3分钟内的汇总)
# 换算逻辑：1小时(60分钟)包含20个3分钟
hourly_max_flow = st.number_input("高峰小时最大断面客流量 (根据上述结果换算)", value=int(max_flow * 20))

col1, col2 = st.columns(2)
with col1:
    capacity = st.selectbox("车型定员 (人/车)", options=[14, 30, 50], index=0)
with col2:
    interval = st.slider("发车间隔 (分钟/班)", min_value=1, max_value=30, value=1, step=1)

# --- 计算逻辑 ---
buses_per_hour = 60 / interval
total_capacity = buses_per_hour * capacity
load_factor = hourly_max_flow / total_capacity

# --- 结果展示 ---
st.subheader("📊 模拟诊断结果")
m1, m2, m3 = st.columns(3)
m1.metric("每小时发车", f"{buses_per_hour:.0f} 班")
m2.metric("每小时总运力", f"{total_capacity:.0f} 人")
m3.metric("预测平均满载率", f"{load_factor * 100:.1f} %")

# 进度条与评价指示
progress_value = float(min(load_factor, 1.0))

if load_factor < 0.5:
    st.error(f"🔴 当前满载率 {load_factor * 100:.1f}%：运力严重浪费，车辆在“烧钱空跑”，建议立刻拉长发车间隔！")
    st.progress(progress_value)
elif 0.5 <= load_factor <= 0.85:
    st.success(f"🟢 当前满载率 {load_factor * 100:.1f}%：运营状态良好，既保证学生舒适度，又兼顾了运营成本。")
    st.progress(progress_value)
else:
    st.warning(f"🟡 当前满载率 {load_factor * 100:.1f}%：车厢极度拥挤，可能会发生滞留现象，需缩短间隔或换大车！")
    st.progress(1.0)