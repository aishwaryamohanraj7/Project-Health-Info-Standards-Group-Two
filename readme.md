# FHIR ETL Pipeline Project

## Project Purpose

This project demonstrates how healthcare data can be extracted, transformed, and integrated using FHIR standards, while ensuring interoperability with legacy systems through HL7 message generation.

---

## Objectives

- Build an end-to-end ETL pipeline using FHIR data  
- Extract patient and clinical data from a FHIR server  
- Transform data using standardized terminologies such as SNOMED CT  
- Establish relationships between clinical concepts  
- Generate HL7 messages for interoperability  
- Present results through a structured and interactive web interface  

---

## ETL Pipeline Overview

### Extract
- Connected to the OpenEMR FHIR API  
- Retrieved patient and clinical data  
- Parsed JSON responses and validated structure  

### Transform
- Cleaned and structured raw data  
- Mapped clinical concepts using SNOMED CT  
- Built parent-child relationships for conditions  
- Standardized data for further processing  

### Load
- Sent transformed data to a target system  
- Generated HL7 v2 messages (ADT format)  
- Validated successful data transmission  

---

## Tasks Performed

### Task 1: Patient Extraction and Parent Condition
- Retrieved patient details from FHIR Patient resource  
- Extracted patient ID and demographic information  
- Mapped COPD using SNOMED CT
- Identified parent condition such as
- Created a Patient resource on Primary care EHR
- Created a Condition (using parent condition) resource on Primary care EHR for the same patient.
### Task 2: Child Condition 
- Mapped COPD using SNOMED CT  
- Identified child conditions such as bronchitis and emphysema  
- Created a Condition (using child condition) resource on Primary care EHR for the same patient.
### Task 3: Observation
- Recorded observations such as blood pressure  
- Structured data using FHIR Observation  

### Task 4: Procedure
- Captured procedure details such as Chest X-ray  
- Stored and validated procedure data  

### Task 5: HL7 Message Generation
- Converted FHIR data into HL7 v2 format  
- Generated MSH, PID, PV1, and DG1 segments  

---

## Key Technologies

- Python  
- FHIR  
- OpenEMR API  
- SNOMED CT  
- HL7 v2  
- HTML, CSS, JavaScript  

---
## Project Structure

```
Project-Health-Info-Standards-Group-Two/
│
├── src/
│   ├── data/
│   ├── __init__.py
│   ├── access_token.py
│   ├── authorization_code.py
│   ├── hl7_message.txt
│   ├── read_token.py
│   ├── refresh_token.py
│   ├── registration.py
│   ├── task_1.py
│   ├── task_2.py
│   ├── task_3.py
│   ├── task_4.py
│   ├── task_5.py
│
├── website/
│   ├── images/
│   ├── assets/
│   ├── about.html
│   ├── etl.html
│   ├── etl_chart.png
│   ├── graph.py
│   ├── index.html
│   ├── insights.html
│   ├── style.css
│   ├── team.html
│
├── main.py
├── .gitignore
├── readme.md
```
```

## How to Run the Project

### 1. Clone the Repository

```bash
git clone https://github.iu.edu/Aismohan/Project-Health-Info-Standards-Group-Two.git
cd Project-Health-Info-Standards-Group-Two
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

Activate:

Mac/Linux:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install
requests
hl7apy
python-dotenv
pandas
numpy
matplotlib
sickit-learn
json
datetime
uuid
All dependencies are listed in requirements.txt
```

---

### 4. Run the Project

```bash
cd src
python main.py
```

---

## Project Website

https://pages.github.iu.edu/Aismohan/Project-Health-Info-Standards-Group-Two/website/index.html

---

## Team Members

| Name | Role |
|------|------|
| Aishwarya Mohanraj | Data Extraction Lead & Web Developer |
| Partha Pratim Seal | Data Engineer & Analyst |
| Sathvika Neeruddula | Team Leader & Transformation Lead |

---

## Summary

This project shows how healthcare data can be processed using FHIR and converted into HL7 for compatibility with legacy systems. It demonstrates a complete ETL workflow along with a web interface for visualization.

---
