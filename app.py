import streamlit as st
import pandas as pd
import hashlib
from core.ai_analyzer import ask_deepseek

from core.data_analyzer import analyze_by_major
from core.data_cleaner import (
    drop_missing_values,
    fill_missing_with_mean,
    fill_missing_with_median,
    drop_duplicate_rows,
    mark_outliers_iqr,
    handle_outliers_iqr,
    convert_data_types,
    compare_dataframes,
    dataframe_to_csv_bytes,
    reset_to_original,
)
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

    # 读取文件并保留原始数据
    file_bytes = uploaded_file.getvalue()

    raw_df = pd.read_csv(uploaded_file)

    file_signature = (
        uploaded_file.name,
        hashlib.sha256(file_bytes).hexdigest()
    )

    if st.session_state.get("uploaded_file_signature") != file_signature:
        st.session_state["uploaded_file_signature"] = file_signature
        st.session_state["original_df"] = raw_df.copy()
        st.session_state["cleaned_df"] = raw_df.copy()
        st.session_state["cleaning_history"] = []

    original_df = st.session_state["original_df"]
    df = st.session_state["cleaned_df"]

    st.success("文件上传成功！原始数据已保留，可在下方进行清洗并导出结果。")

    # 数据预览
    st.subheader("数据预览（当前数据）")
    st.dataframe(df.head())

    # 数据基本信息
    st.subheader("数据基本信息（当前数据）")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("数据行数", len(df))

    with col2:
        st.metric("数据列数", len(df.columns))

    st.subheader("🧹 数据清洗")
    st.caption("以下操作均在当前清洗结果上继续执行；原始数据始终保留，可随时恢复或导出。")

    clean_col1, clean_col2, clean_col3 = st.columns(3)

    with clean_col1:
        if st.button("删除缺失值行", use_container_width=True):
            st.session_state["cleaned_df"] = drop_missing_values(df)
            st.session_state["cleaning_history"].append("删除缺失值行")
            st.rerun()

        if st.button("均值填充", use_container_width=True):
            st.session_state["cleaned_df"] = fill_missing_with_mean(df)
            st.session_state["cleaning_history"].append("均值填充（数值列）")
            st.rerun()

        if st.button("删除重复数据", use_container_width=True):
            st.session_state["cleaned_df"] = drop_duplicate_rows(df)
            st.session_state["cleaning_history"].append("删除重复数据")
            st.rerun()

    with clean_col2:
        if st.button("中位数填充", use_container_width=True):
            st.session_state["cleaned_df"] = fill_missing_with_median(df)
            st.session_state["cleaning_history"].append("中位数填充（数值列）")
            st.rerun()

        outlier_method_label = st.selectbox(
            "异常值处理方式",
            options=["标记异常值", "截断到上下界", "删除异常值行", "用中位数替换异常值", "用均值替换异常值"],
            index=0,
        )
        outlier_method_map = {
            "标记异常值": "mark",
            "截断到上下界": "cap",
            "删除异常值行": "remove",
            "用中位数替换异常值": "median",
            "用均值替换异常值": "mean",
        }
        if st.button("异常值标记与处理", use_container_width=True):
            selected_method = outlier_method_map[outlier_method_label]
            if selected_method == "mark":
                st.session_state["cleaned_df"] = mark_outliers_iqr(df)
            else:
                st.session_state["cleaned_df"] = handle_outliers_iqr(df, method=selected_method)
            st.session_state["cleaning_history"].append(outlier_method_label)
            st.rerun()

    with clean_col3:
        convertible_columns = df.columns.tolist()
        if convertible_columns:
            target_column = st.selectbox("选择要转换的列", options=convertible_columns, key="convert_column")
            target_type_label = st.selectbox(
                "目标数据类型",
                options=["自动推断", "整数 (int)", "浮点数 (float)", "字符串 (str)", "布尔值 (bool)", "日期时间 (datetime)", "分类 (category)"],
                index=0,
                key="convert_type",
            )
            if st.button("数据类型转换", use_container_width=True):
                if target_type_label == "自动推断":
                    converted = convert_data_types(df[[target_column]], infer_objects=True)
                    updated_df = df.copy()
                    updated_df[target_column] = converted[target_column]
                    st.session_state["cleaned_df"] = updated_df
                    st.session_state["cleaning_history"].append(f"数据类型转换：{target_column} -> 自动推断")
                else:
                    type_map = {
                        "整数 (int)": "int",
                        "浮点数 (float)": "float",
                        "字符串 (str)": "str",
                        "布尔值 (bool)": "bool",
                        "日期时间 (datetime)": "datetime",
                        "分类 (category)": "category",
                    }
                    st.session_state["cleaned_df"] = convert_data_types(
                        df,
                        column_types={target_column: type_map[target_type_label]}
                    )
                    st.session_state["cleaning_history"].append(
                        f"数据类型转换：{target_column} -> {target_type_label}"
                    )
                st.rerun()
        else:
            st.info("当前数据没有可转换的列")

        if st.button("恢复为原始数据", use_container_width=True):
            st.session_state["cleaned_df"] = reset_to_original(original_df)
            st.session_state["cleaning_history"] = []
            st.rerun()

    if st.session_state.get("cleaning_history"):
        st.write("**已执行的清洗操作：** " + " → ".join(st.session_state["cleaning_history"]))
    else:
        st.info("尚未执行清洗操作，当前显示的是原始数据副本。")

    st.subheader("📊 清洗前后数据对比")
    comparison = compare_dataframes(original_df, df)

    st.write("#### 总体对比")
    st.dataframe(comparison["summary"], use_container_width=True)

    compare_detail_col1, compare_detail_col2 = st.columns(2)
    with compare_detail_col1:
        st.write("#### 缺失值变化")
        st.dataframe(comparison["missing_values"], use_container_width=True)
    with compare_detail_col2:
        st.write("#### 数据类型变化")
        st.dataframe(comparison["dtypes"], use_container_width=True)

    with st.expander("查看原始数据预览（保留）"):
        st.dataframe(original_df, use_container_width=True)

    with st.expander("查看当前清洗结果预览"):
        st.dataframe(df, use_container_width=True)

    st.subheader("💾 原始数据保留与清洗结果导出")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            label="下载原始数据 CSV",
            data=dataframe_to_csv_bytes(original_df),
            file_name="original_data.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            label="下载清洗结果 CSV",
            data=dataframe_to_csv_bytes(df),
            file_name="cleaned_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.subheader("🔍 数据质量报告（当前数据）")

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
    st.subheader("数据统计（当前数据）")
    st.write(df.describe(include="all"))

    # 成绩分析
    if "成绩" in df.columns and pd.api.types.is_numeric_dtype(df["成绩"]) and not df["成绩"].dropna().empty:

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

        if "专业" in df.columns and "姓名" in df.columns and "课程" in df.columns:
            major_stats = analyze_by_major(df)
            st.dataframe(major_stats)

            # 专业成绩可视化
            st.subheader("📊 各专业平均成绩对比")
            fig = create_major_chart(major_stats)
            st.pyplot(fig)

            # 各课程平均成绩图表
            if "课程" in df.columns:
                st.subheader("📚 各课程平均成绩对比")
                course_fig = create_course_chart(df)
                st.pyplot(course_fig)
        else:
            st.info("当前数据缺少“专业/姓名/课程”列，无法生成完整的成绩分组分析图表。")
    elif "成绩" in df.columns:
        st.info("“成绩”列当前不是可用于统计的数值数据，请先进行数据类型转换或清洗。")

    # AI 智能分析
    st.markdown("---")
    st.subheader("🤖 AI 智能数据分析")

    st.write("你可以用自然语言向 AI 提问，让它帮助你理解当前数据。")

    ai_question = st.text_area(
        "请输入你的分析问题",
        placeholder="例如：哪个专业的平均成绩最高？",
        key="ai_question"
    )

    if st.button("开始 AI 分析", use_container_width=True):
        if not ai_question.strip():
            st.warning("请先输入分析问题。")
        else:
            with st.spinner("AI 正在分析，请稍候..."):
                try:
                    # 生成当前数据的统计摘要
                    numeric_columns = df.select_dtypes(
                        include="number"
                    ).columns.tolist()

                    
                    data_context = f"""
                    数据行数：{len(df)}
                    数据列数：{len(df.columns)}
                    列名：{df.columns.tolist()}

                    数据统计：
                    {df.describe(include="all").to_string()}
                    """

                    #生成数据质量提示
                    quality_notes = []

                    # 1. 缺失值检查
                    missing_counts = df.isna().sum()
                    for column, count in missing_counts.items():
                        if count > 0:
                             quality_notes.append(
                                f"列“{column}”存在 {count} 个缺失值。"
                           )

                    # 2. 完全重复行检查
                    duplicate_count = int(df.duplicated().sum())

                    if duplicate_count > 0:
                        quality_notes.append(
                            f"数据中存在 {duplicate_count} 条完全重复的记录。"
                        )

                    # 3. 成绩范围检查
                    invalid_scores = 0
                    if "成绩" in df.columns:
                        scores = pd.to_numeric(df["成绩"], errors="coerce")
                        invalid_scores = int((scores > 100).sum())

                    if invalid_scores > 0:
                        quality_notes.append(
                             f"成绩列有 {invalid_scores} 条记录超过100分。"
                            "如果采用百分制，这些记录可能存在异常，"
                            "需要核实原始数据。"
                        )

                    # 将质量信息加入数据摘要
                    if quality_notes:
                        data_context += "\n数据质量提示：\n"
                        data_context += "\n".join(quality_notes)
                    else:
                        data_context += "\n数据质量提示：未发现上述几类问题。"


                    # 增加数值列的分组分析信息
                    if "专业" in df.columns and numeric_columns:
                        for column in numeric_columns:
                            data_context += (
                                f"\n各专业的{column}平均值：\n"
                            )
                            data_context += (
                                df.groupby("专业")[column]
                                .mean()
                                .to_string()
                            )

                    # 调用 DeepSeek
                    result = ask_deepseek(
                        ai_question,
                        data_context
                    )

                    st.success("AI 分析完成！")
                    st.markdown(result)

                except Exception as e:
                    st.error(f"AI 分析失败：{e}")

else:
    st.info("请先上传一个 CSV 文件。")
