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

import matplotlib.pyplot as plt


labels = ['Success', 'Failure']
values = [85, 15]

plt.figure()

plt.pie(values, labels=labels, autopct='%1.1f%%')

plt.title("API Request Success vs Failure")

plt.tight_layout()
plt.savefig("success_pie.png")  # saved image
plt.show()