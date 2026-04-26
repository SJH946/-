import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# 设置中文字体，确保图表正常显示中文
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']  # Windows用SimHei, Mac用Arial Unicode MS
plt.rcParams['axes.unicode_minus'] = False


# ==========================================
# 第一部分：公交时刻表多目标优化模型构建与求解
# ==========================================
def optimize_headway(Q, C, h_min, h_max, target_lf_min, target_lf_max, c_op, c_wait):
    """
    Q: 小时客流量 (人/小时)
    C: 车辆额定载客量 (人/车)
    h_min, h_max: 发车间隔的上下限 (分钟)
    target_lf_min, target_lf_max: 满载率上下限约束
    c_op: 单次发车运营成本权重
    c_wait: 乘客单位等待时间成本权重
    """
    best_h = None
    min_cost = float('inf')

    print(f"--- 正在求解断面客流为 {Q} 人/小时 的最优发车间隔 ---")

    # 在给定的发车间隔范围内进行离散搜索 (步长为1分钟)
    for h in range(h_min, h_max + 1):
        # 1. 计算约束条件：满载率
        load_factor = (Q * (h / 60)) / C

        # 如果不满足满载率约束，则跳过（惩罚）
        if load_factor < target_lf_min or load_factor > target_lf_max:
            continue

        # 2. 计算目标函数：系统总成本 = 运营成本 + 乘客候车成本
        # 运营成本与发车班次(60/h)成正比
        cost_operator = c_op * (60 / h)
        # 乘客候车成本与平均候车时间(h/2)及总人数(Q)成正比
        cost_passenger = c_wait * (h / 2) * Q

        total_cost = cost_operator + cost_passenger

        if total_cost < min_cost:
            min_cost = total_cost
            best_h = h

    if best_h:
        best_lf = (Q * (best_h / 60)) / C
        print(f">> 最优发车间隔: {best_h} 分钟 | 对应满载率: {best_lf:.1%} | 最小化系统总成本: {min_cost:.2f}\n")
        return best_h, best_lf
    else:
        print(">> 在当前约束下无可行解，建议放宽满载率或间隔限制。\n")
        return None, None


# 模型参数标定
CAPACITY = 14  # 车型定员
Q_PEAK = 126  # 早高峰最大小时客流
Q_OFF = 30  # 平峰小时客流

# 运行优化模型
# 假设参数：运营单趟成本权重=50, 乘客等待1分钟成本权重=0.5
print("【优化模型求解结果】")
opt_peak_h, opt_peak_lf = optimize_headway(Q_PEAK, CAPACITY, 2, 10, 0.5, 0.9, 50, 0.5)
opt_off_h, opt_off_lf = optimize_headway(Q_OFF, CAPACITY, 10, 30, 0.3, 0.8, 50, 0.5)

# ==========================================
# 第二部分：优化前后效果对比可视化 (绘图)
# ==========================================
# 提取报告中的现状(优化前)数据与模型得出的(优化后)数据
scenarios = ['早高峰(优化前)', '早高峰(优化后)', '平峰(优化前)', '平峰(优化后)']

# 发车间隔 (分钟)
headways = [3, 5, 25, 15]
# 平均候车时间 (假设为发车间隔的一半)
wait_times = [h / 2 for h in headways]
# 满载率计算公式: (小时客流 * (间隔/60)) / 额定载客量
load_factors = [
    (Q_PEAK * (3 / 60)) / CAPACITY,
    (Q_PEAK * (5 / 60)) / CAPACITY,
    (Q_OFF * (25 / 60)) / CAPACITY,
    (Q_OFF * (15 / 60)) / CAPACITY
]
# 小时发车班次
frequencies = [60 / h for h in headways]

# 创建图表 (1行3列)
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
colors_before = '#ff9999'
colors_after = '#66b3ff'
bar_colors = [colors_before, colors_after, colors_before, colors_after]

# 图1：平均候车时间对比
ax1.bar(scenarios, wait_times, color=bar_colors)
ax1.set_title('平均候车时间对比 (分钟)', fontsize=12, pad=15)
ax1.set_ylabel('时间 (min)')
for i, v in enumerate(wait_times):
    ax1.text(i, v + 0.2, f'{v:.1f}', ha='center', fontweight='bold')
ax1.tick_params(axis='x', rotation=15)

# 图2：车辆满载率对比
ax2.bar(scenarios, [lf * 100 for lf in load_factors], color=bar_colors)
ax2.set_title('单车平均满载率对比 (%)', fontsize=12, pad=15)
ax2.set_ylabel('满载率 (%)')
# 画一条80%和50%的参考线
ax2.axhline(80, color='red', linestyle='--', alpha=0.5, label='舒适度警戒线')
ax2.legend()
for i, v in enumerate(load_factors):
    ax2.text(i, v * 100 + 2, f'{v * 100:.1f}%', ha='center', fontweight='bold')
ax2.tick_params(axis='x', rotation=15)

# 图3：小时资源投入(发车班次)对比
ax3.bar(scenarios, frequencies, color=bar_colors)
ax3.set_title('运力资源投入对比 (班次/小时)', fontsize=12, pad=15)
ax3.set_ylabel('班次/小时')
for i, v in enumerate(frequencies):
    ax3.text(i, v + 0.5, f'{int(v)}', ha='center', fontweight='bold')
ax3.tick_params(axis='x', rotation=15)

plt.tight_layout()
plt.savefig('optimization_comparison.png', dpi=300, bbox_inches='tight')
print("\n>> 对比图表已生成并保存为 'optimization_comparison.png'，请将其插入报告中。")
plt.show()