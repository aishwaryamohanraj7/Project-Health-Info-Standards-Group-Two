#patients-bar graph
import matplotlib.pyplot as plt

resources = ['Patient', 'Condition', 'Observation', 'Procedure']
counts = [10, 25, 40, 15]

plt.figure()

plt.bar(resources, counts)

plt.title("FHIR Resource Distribution")
plt.xlabel("Resource Type")
plt.ylabel("Count")

plt.tight_layout()
plt.savefig("etl_chart.png")
plt.show()

#procedures-line graph
import matplotlib.pyplot as plt
from collections import Counter


years = [
    2024, 2024, 2023,
    2021, 2021, 2021, 2021, 2021, 2021, 2021,
    2020, 2020, 2020, 2020, 2020,
    2018, 2018, 2018, 2018, 2018,
    2016, 2016, 2016,
    2015, 2015,
    2014, 2014
]


year_counts = Counter(years)

sorted_years = sorted(year_counts.keys())
counts = [year_counts[y] for y in sorted_years]


plt.figure()
plt.plot(sorted_years, counts, marker='o')

plt.title("Procedures Over Time")
plt.xlabel("Year")
plt.ylabel("Number of Procedures")

plt.grid()


plt.savefig("procedure_chart.png", dpi=300, bbox_inches='tight')

plt.show()