# FHIR ETL Pipeline Project

## Project Purpose

The purpose of this project is to demonstrate how healthcare data can be extracted, transformed, and integrated using FHIR standards while ensuring interoperability with legacy systems through HL7 message generation.

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

### Task 1: Patient Extraction
- Retrieved patient details from FHIR Patient resource  
- Extracted patient ID and demographic information  
- Identified relevant patient data for further processing  

### Task 2: Condition Mapping
- Mapped COPD using SNOMED CT  
- Identified related child conditions (e.g., bronchitis, emphysema)  
- Established hierarchical relationships  

### Task 3: Observation
- Recorded patient observations (e.g., blood pressure)  
- Structured data using FHIR Observation format  
- Validated measurement values  

### Task 4: Procedure
- Captured procedure details (e.g., Chest X-ray)  
- Used FHIR Procedure resource structure  
- Stored and validated procedure data  

### Task 5: HL7 Message Generation
- Converted FHIR data into HL7 v2 format  
- Generated key segments (MSH, PID, PV1, DG1)  
- Ensured compatibility with legacy systems  

---

## Key Technologies

- Python  
- FHIR (Fast Healthcare Interoperability Resources)  
- OpenEMR FHIR API  
- SNOMED CT (clinical terminology)  
- HL7 v2 (message standard)  
- HTML, CSS, JavaScript (web interface)  
- GitHub Pages (deployment)  

---

## Project Summary

This project demonstrates how healthcare data can be integrated across systems using modern interoperability standards. By combining FHIR for data exchange and HL7 for legacy compatibility, the ETL pipeline provides a structured approach to managing clinical information. The web interface further enhances understanding by presenting each stage of the pipeline along with code outputs and visualizations.

---

## Project Website

https://pages.github.iu.edu/Aismohan/Project-Health-Info-Standards-Group-Two/website/index.html


---