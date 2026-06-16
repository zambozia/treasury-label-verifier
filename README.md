Alcohol Label Verification App
OCR-assisted alcohol label verification prototype for Treasury label review workflows.
Quick Start
Live Application
https://treasury-label-verifier-docker.onrender.com/
GitHub Repository
https://github.com/zambozia/treasury-label-verifier
Test Data
Sample CSV datasets and label images are included in:
sample-data/
sample-labels/
sample-batches/
Typical Workflow
Upload application CSV
Upload label images
Run verification
Review results
Export CSV reports
Local Installation
## Running Locally

### Clone Repository

git clone https://github.com/zambozia/treasury-label-verifier

### Install Dependencies

pip install -r requirements.txt

### Install Tesseract OCR

Windows:
https://github.com/UB-Mannheim/tesseract/wiki

### Run

streamlit run app.py 

Overview
The Alcohol Label Verification App is a batch-first prototype designed to assist Alcohol and Tobacco Tax and Trade Bureau (TTB) compliance agents with reviewing alcohol beverage labels.
The application uses local Optical Character Recognition (OCR) to extract text from uploaded label images, matches each label against application records provided through a CSV file, and validates required label fields.
The goal is to reduce repetitive manual verification work while maintaining human oversight for compliance decisions.
This prototype was developed as a proof of concept and is not intended to replace human review.

Human-in-the-Loop Design
This application is designed as a decision-support tool rather than an automated compliance authority.
The system assists compliance agents by identifying potential matches, mismatches, missing information, and items that may require additional review.
The application may recommend:
Pass
Fail
Needs Review
Final compliance determinations remain the responsibility of the reviewing compliance agent.
This design reflects the principle that artificial intelligence should augment human expertise rather than replace regulatory judgment.

Stakeholder Traceability
The prototype design was guided directly by stakeholder feedback.
Stakeholder
Concern
Prototype Response
Sarah Chen
Fast processing and ease of use
Local OCR, streamlined workflow, target under five seconds per label
Janet
Batch processing support
Batch-first workflow supporting 5–20 labels
Marcus Williams
Restricted network environments
Local-first architecture with no required external AI APIs
Dave Morrison
Human judgment and formatting differences
Fuzzy matching and human review workflow
Jenny Park
Strict government warning requirements
Strict warning validation and review flags


Problem Statement
TTB agents currently spend significant time manually comparing information submitted in applications against information printed on alcohol labels.
Common verification tasks include:
Brand name verification
Class/type verification
Alcohol content verification
Net contents verification
Government warning verification
Many of these tasks involve repetitive comparisons that can potentially be automated.
This prototype demonstrates how OCR and automated validation can help agents identify potential issues more quickly.

Features
Batch Verification Workflow
Users can:
Upload application records through CSV
Upload one or more label images
Automatically match labels to application records
Review field-by-field validation results
Export verification results as CSV
Single Label Test Mode
A simplified single-label workflow is available for testing, demonstrations, and troubleshooting.
OCR Text Extraction
The application extracts readable text from label images using local OCR technology.
Validation Engine
The system compares extracted values against expected values using:
Fuzzy matching
Exact matching
Normalized matching
Strict matching
depending on the field being evaluated.
Compliance Results
The application displays:
Expected values
Detected values
Match status
Confidence information
Review notes
Processing times

Architecture
User Interface
Streamlit
Application Logic
Python
OCR Engine
Tesseract OCR
Text Similarity
RapidFuzz
Deployment
Render
Supporting Libraries
Pandas
Pillow

Why Local OCR
This prototype prioritizes local OCR and rule-based validation rather than reliance on external AI APIs.
Reasons include:
Reduced latency and faster processing times
Fewer external dependencies
Improved reliability in restricted network environments
Easier future deployment within government infrastructure
More predictable and explainable validation behavior
The prototype is intentionally designed so that core functionality can operate without requiring outbound requests to third-party AI services.

System Workflow
User uploads application records via CSV
User uploads one or more label images
OCR extracts text from each label
Text normalization standardizes OCR output
Record matching identifies the most likely application record
Validation engine compares extracted values against application data
Recommendation engine generates Pass, Fail, or Needs Review
Results dashboard displays findings
Results may be exported as CSV

Explainability and Validation Transparency
Every validation result generated by the application includes:
Expected Value
Detected Value
Validation Method
Confidence Score
Explanation
Example:
Field: Brand Name
Expected:
STONE'S THROW
Detected:
Stone's Throw
Validation Method:
Fuzzy Match
Confidence:
100%
Explanation:
Brand name matches after text normalization.
This approach allows reviewers to understand how results were generated and supports auditability, transparency, and reviewer confidence.

Record Matching
The application attempts to identify the most likely application record for each uploaded label.
Confidence Thresholds
95% and above:
Auto Match
70%–94%:
Needs Review
Below 70%:
No Match
Record matching recommendations are advisory only.
Final record assignment remains the responsibility of the reviewing compliance agent.

Validation Rules
Brand Name
Match Type: Fuzzy Match
Reason:
Minor formatting differences should not trigger failures.
Example:
Expected:
STONE'S THROW
Detected:
Stone's Throw
Result:
Pass
Class / Type
Match Type: Fuzzy Match
Reason:
Formatting and capitalization differences are generally not compliance issues.
Alcohol Content
Match Type: Exact Match
Reason:
Alcohol content is a regulated value and must be accurate.
Net Contents
Match Type: Exact Match
Reason:
Net contents must match application data.
Government Warning
Match Type: Strict Match
Reason:
Federal regulations require specific warning language.

Beverage Type Scope
TTB requirements vary by beverage type, including beer, wine, and distilled spirits.
For this prototype, validation focuses on the common label elements shared across beverage categories.
Supported Beverage Types:
Beer
Wine
Distilled Spirits
Unknown
The beverage type field is included for future extensibility but does not currently activate beverage-specific validation rules.
Future versions may include separate validation engines for each beverage category.

CSV Schema
Required Fields
record_id
brand_name
class_type
alcohol_content
net_contents
government_warning
Optional Fields
bottler_producer
country_of_origin
beverage_type
If required columns are missing, the application will display a validation error and stop processing.

Assumptions
The application assumes:
Uploaded images contain readable label text
Images are reasonably clear and in focus
Application data is supplied through CSV records
Images may be processed individually or in batches
Human reviewers remain responsible for final compliance decisions

Design Decisions
Local OCR Instead of Cloud OCR
The prototype uses local OCR rather than cloud-based AI services.
Reasons:
Reduced dependency on external services
Lower latency
Better compatibility with restricted network environments
Easier future deployment within government environments
Rule-Based Validation
The prototype uses deterministic validation rules rather than relying entirely on generative AI.
Reasons:
Predictable results
Easier auditing
Better transparency
Simpler troubleshooting
Human-in-the-Loop Review
The application is designed to assist reviewers, not replace them.
Labels with uncertain results are routed for manual review.
Sequential Batch Processing
Labels are processed one at a time.
Results appear as each label completes processing.
This improves responsiveness and supports the stakeholder requirement for rapid feedback.

Limitations
This prototype does not:
Integrate with COLAs Online
Store historical application data
Perform final regulatory approval
Handle every possible label format
Guarantee perfect OCR performance
Validate beverage-specific regulations
Validate font size or font weight requirements
Validate exact label layout requirements
Support production-scale batch workloads
Poor image quality may reduce extraction accuracy.

Future Integration
In a production environment, expected application data would likely originate from COLAs Online or another system of record.
CSV uploads are used in this prototype to simulate application data while remaining independent of existing government systems.
Future versions may support direct integration with external systems once authorization and security requirements are defined.

Future Improvements
Potential future enhancements include:
Advanced image preprocessing
Label region detection
Beverage-specific validation rules
Bottler/producer validation
Country-of-origin validation
Font and layout validation
Confidence-based workflow routing
Integration with TTB review systems
Audit logging
Accessibility improvements
FedRAMP-compliant deployment architecture
Larger batch processing workflows (200–500+ labels)
Manual record assignment workflows

Test Data
The repository includes sample data demonstrating:
Valid labels
Invalid labels
Missing warning statements
Brand mismatches
ABV mismatches
Poor-quality images
Record matching scenarios
The repository also includes sample application datasets that can be loaded into the application for testing.
These resources allow reviewers to evaluate the prototype without creating their own test materials.

Repository Structure
app.py
docs/
ocr/
matching/
validation/
utils/
sample-labels/
sample-data/
sample-batches/
README.md


Approach and Technical Decisions
The project was developed as an OCR-assisted decision-support tool rather than a fully automated compliance system.
Several approaches were evaluated during development. Early versions prioritized OCR accuracy but required more than 50 seconds to process some labels. Later versions prioritized speed but reduced extraction accuracy.
The final implementation balances speed and accuracy by:
Using multiple OCR preprocessing passes
Applying text normalization and fuzzy matching
Limiting OCR execution time per label
Preserving human review workflows
Providing explainable validation results
This approach achieved reliable field extraction while maintaining processing times generally below five seconds per label on the deployed environment.
The application intentionally keeps the reviewer in control of all final compliance decisions.

Development Challenges and Lessons Learned
Several challenges were encountered during development:
OCR Accuracy
Early OCR implementations struggled with decorative fonts, low-contrast labels, and complex layouts. Multiple preprocessing techniques and OCR pass strategies were evaluated before reaching acceptable performance.
OCR Performance
One iteration achieved excellent extraction accuracy but required more than 50 seconds to process certain labels. The final implementation restored the original multi-pass OCR workflow and optimized execution by limiting OCR threading, reducing processing times to under five seconds per label while maintaining accuracy.
Deployment
The application was initially deployed using a standard Python deployment environment. OCR dependencies proved difficult to support reliably in that configuration. Deployment was migrated to a Docker-based architecture, allowing Tesseract OCR and supporting libraries to run consistently.
Record Matching
Several iterations were required to balance fuzzy matching confidence thresholds while preserving explainability and minimizing false positives.
Human Review Workflow
The final design intentionally routes uncertain results to a "Needs Review" state rather than forcing automated decisions. This preserves reviewer oversight and aligns with the project's compliance-oriented goals.

Version: 1.0
Status: Submission Candidate
Last Updated: June 2026 
## Prototype Results

Testing was performed using sample alcohol beverage labels representing beer, wine, distilled spirits, and imported products.

Final deployed performance achieved:

- Batch processing support for multiple labels
- Processing times generally under 5 seconds per label
- Successful validation of required label fields
- Explainable validation results
- Human-review workflow for uncertain cases

The prototype intentionally favors transparency and reviewer oversight over fully automated approval decisions.

