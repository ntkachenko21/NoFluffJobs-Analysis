import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from processing import load_data


def apply_common_style():
    """Apply common styling to all plots"""
    plt.grid(True, alpha=0.3, axis="y")
    for spine in plt.gca().spines.values():
        spine.set_linewidth(1.5)
    plt.tight_layout()


def plot_top_10_skills(df: pd.DataFrame):
    # Explode and get top 10 skills
    skills_series = df.explode("requirements")["requirements"]
    top_skills = skills_series.value_counts().head(10)

    # Create figure with bars
    plt.figure(figsize=(12, 8))
    bars = plt.bar(
        top_skills.index,
        top_skills.values,
        color="blue",
        alpha=0.6,
        edgecolor="black",
        linewidth=0.5
    )

    # Set numbers of mentions every skill in data (above the bar)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + 5,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11)

    # Set percentages of mentions every skill in all data (above the number of mentions)
    total_jobs = len(df)
    for i, bar in enumerate(bars):
        height = bar.get_height()
        percentage = (height / total_jobs) * 100
        plt.text(bar.get_x() + bar.get_width() / 2,
                 height + 30,
                 f"({percentage:.1f}%)",
                 ha="center",
                 va="bottom",
                 fontsize=11,
                 color="darkred")

    # Add text to figure
    plt.title(
        "Top 10 Required Skills in Job Postings",
        fontsize=16,
        fontweight="bold",
        pad=20
    )
    plt.ylabel(
        f"Number of Mentions ({total_jobs} vacancies)",
        fontsize=12,
        fontweight="bold"
    )
    plt.xlabel(
        "Skills",
        fontsize=12,
        fontweight="bold"
    )

    # Rotate text of every skill
    plt.xticks(rotation=45, ha="right")

    plt.ylim(0, max(top_skills.values) * 1.15)

    # Apply common styling
    apply_common_style()
    plt.show()


def plot_salary_statistics(df: pd.DataFrame):
    # Filter data and calculate statistics
    salary_df = df.dropna(subset=["salary_avg"])
    grouped_by_seniority = salary_df.groupby("seniority")
    median_salary_by_seniority = grouped_by_seniority["salary_avg"].median().sort_values()
    sample_sizes = salary_df.groupby("seniority").size()

    # Create figure with bars
    plt.figure(figsize=(12, 8))
    bars = plt.bar(
        median_salary_by_seniority.index,
        median_salary_by_seniority.values,
        color="blue",
        alpha=0.6,
        edgecolor="black",
        linewidth=0.5
    )

    # Add salary values above bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 500,
            f"{height:,.0f} PLN",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11
        )

    # Add sample sizes above salary values
    for i, bar in enumerate(bars):
        height = bar.get_height()
        seniority = median_salary_by_seniority.index[i]
        sample_size = sample_sizes[seniority]
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1500,
            f"(n={sample_size})",
            ha="center",
            va="bottom",
            fontsize=11,
            color="darkred"
        )

    # Add text to figure
    plt.title(
        "Median Salary by Seniority Level",
        fontsize=16,
        fontweight="bold",
        pad=20
    )
    plt.ylabel(
        "Median Salary (PLN)",
        fontsize=12,
        fontweight="bold"
    )
    plt.xlabel(
        "Seniority Level",
        fontsize=12,
        fontweight="bold"
    )

    # Format Y-axis with thousands separator
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    plt.ylim(0, max(median_salary_by_seniority.values) * 1.15)

    # Apply common styling
    apply_common_style()
    plt.show()


if __name__ == "__main__":
    data = load_data()
    plot_top_10_skills(data)
    plot_salary_statistics(data)
