import streamlit as st
import pandas as pd

from core.data_analyzer import analyze_by_major

from core.data_quality import (
    check_missing_values,
    check_duplicate_rows,
    check_outliers_iqr,
    check_data_types
)

from core.chart_generator import (
    create_major_chart,
    create_course_chart
)
# 页面配置
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide"
)

# 页面标题
st.title("📊 AI 智能数据分析助手")
st.write("欢迎使用 AI Data Analyst！")
st.markdown("---")

# 上传文件
uploaded_file = st.file_uploader(
    "请上传 CSV 文件",
    type=["csv"]
)

if uploaded_file is not None:

    # 读取文件
    df = pd.read_csv(uploaded_file)

    st.success("文件上传成功！")

    # 数据预览
    st.subheader("数据预览")
    st.dataframe(df.head())

    # 数据基本信息
    st.subheader("数据基本信息")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("数据行数", len(df))

    with col2:
        st.metric("数据列数", len(df.columns))


    st.subheader("🔍 数据质量报告")

    # 1. 缺失值检测
    st.write("### 缺失值检测")
    missing_stats = check_missing_values(df)
    st.dataframe(missing_stats)

    # 2. 重复值检测
    st.write("### 重复值检测")
    duplicate_stats = check_duplicate_rows(df)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("重复行数量", duplicate_stats["重复行数量"])
    with col2:
        st.metric("重复行比例", f'{duplicate_stats["重复行比例(%)"]}%')

    # 3. 异常值检测
    st.write("### 异常值检测")
    outlier_stats = check_outliers_iqr(df)

    if outlier_stats:
        outlier_table = pd.DataFrame(outlier_stats).T
        st.dataframe(outlier_table)
    else:
        st.info("没有可检测的数值列")

    # 4. 数据类型检查
    st.write("### 数据类型检查")
    type_stats = check_data_types(df)
    st.dataframe(type_stats)




    # 数据统计
    st.subheader("数据统计")
    st.write(df.describe())

    # 成绩分析
    if "成绩" in df.columns:

        st.subheader("📊 成绩分析")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "平均成绩",
                round(df["成绩"].mean(), 2)
            )

        with col2:
            st.metric(
                "最高成绩",
                df["成绩"].max()
            )

        with col3:
            st.metric(
                "最低成绩",
                df["成绩"].min()
            )

        # 调用独立的数据分析模块
        st.subheader("📚 各专业成绩分析")

        major_stats = analyze_by_major(df)

        st.dataframe(major_stats)

        # 专业成绩可视化
        st.subheader("📊 各专业平均成绩对比")

        fig = create_major_chart(major_stats)

        st.pyplot(fig)
        # 各课程平均成绩图表
        st.subheader("📚 各课程平均成绩对比")

        course_fig = create_course_chart(df)

        st.pyplot(course_fig)
else:
    st.info("请先上传一个 CSV 文件。")
