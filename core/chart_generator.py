
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# 直接指定 Windows 中文字体文件
font = FontProperties(
    fname=r"C:\Windows\Fonts\msyh.ttc"
)

plt.rcParams["axes.unicode_minus"] = False


def create_major_chart(major_stats):

    # 创建画布
    fig, ax = plt.subplots(figsize=(8, 5))

    majors = major_stats.index
    scores = major_stats["平均成绩"]

    # 绘制柱状图
    ax.bar(majors, scores)

    # 设置标题和坐标轴字体
    ax.set_title(
        "各专业平均成绩对比",
        fontproperties=font
    )

    ax.set_xlabel(
        "专业",
        fontproperties=font
    )

    ax.set_ylabel(
        "平均成绩",
        fontproperties=font
    )

    # 设置横坐标中文字体
    ax.set_xticks(range(len(majors)))
    ax.set_xticklabels(
        majors,
        fontproperties=font
    )

    ax.set_ylim(0, 100)

    # 显示成绩数值
    for i, score in enumerate(scores):
        ax.text(
            i,
            score + 1,
            f"{score:.2f}",
            ha="center"
        )

    fig.tight_layout()

    return fig


def create_course_chart(df):

    # 按课程计算平均成绩
    course_avg = df.groupby("课程")["成绩"].mean()

    # 创建画布
    fig, ax = plt.subplots(figsize=(8, 5))

    # 绘制柱状图
    ax.bar(course_avg.index, course_avg.values)

    # 设置标题和坐标轴
    ax.set_title(
        "各课程平均成绩对比",
        fontproperties=font
    )

    ax.set_xlabel(
        "课程",
        fontproperties=font
    )

    ax.set_ylabel(
        "平均成绩",
        fontproperties=font
    )

    # 设置纵坐标范围
    ax.set_ylim(0, 100)

    # 显示成绩数值
    for i, score in enumerate(course_avg.values):
        ax.text(
            i,
            score + 1,
            f"{score:.2f}",
            ha="center"
        )

    fig.tight_layout()

    return fig

