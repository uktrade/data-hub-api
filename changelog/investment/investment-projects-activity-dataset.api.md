The `GET /v4/dataset/investment-projects-activity-dataset` has been added. The endpoint returns SPI report records for 
corresponding investment projects. The response has following fields:
 
  - investment_project_id
  - enquiry_processed
  - enquiry_type
  - enquiry_processed_by_id
  - assigned_to_ist
  - project_manager_assigned
  - project_manager_assigned_by_id
  - project_moved_to_won
  - aftercare_offered_on
  - propositions

    The propositions is an array with following fields:
    
    - deadline
    - status
    - modified_on
    - adviser_id
