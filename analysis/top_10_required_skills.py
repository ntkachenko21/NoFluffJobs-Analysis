import json
import pandas as pd
import matplotlib.pyplot as plt

with open("nofluff_jobs_extended_930_jobs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)
skills_series = df.explode("requirements")["requirements"]
top_skills = skills_series.value_counts().head(10)

plt.figure(figsize=(12, 8))
bars = plt.bar(
    top_skills.index,
    top_skills.values,
    color="blue",
    alpha=0.6,
    edgecolor="black",
    linewidth=0.5
)

for i, bar in enumerate(bars):
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        height + 5,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=11)

total_jobs = len(df)
for i, bar in enumerate(bars):
    height = bar.get_height()
    percentage = (height / total_jobs) * 100
    plt.text(bar.get_x() + bar.get_width()/2,
    height + 30,
    f"({percentage:.1f}%)",
    ha="center",
    va="bottom",
    fontsize=11,
    color="darkred")

plt.title(
    "Top 10 Required Skills in Job Postings",
    fontsize=16,
    fontweight="bold",
    pad=20
)
plt.ylabel(
    "Number of Mentions (930 vacancies)",
    fontsize=12,
    fontweight="bold"
)
plt.xlabel(
    "Skills",
    fontsize=12,
    fontweight="bold"
)

plt.xticks(rotation=45, ha="right")

plt.grid(True, alpha=0.3, axis="y")

plt.ylim(0, max(top_skills.values) * 1.15)

for spine in plt.gca().spines.values():
    spine.set_linewidth(1.5)

plt.tight_layout()

plt.show()
