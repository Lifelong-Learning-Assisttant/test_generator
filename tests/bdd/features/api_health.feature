Feature: API Health Check
  As a system administrator
  I want to check the API health status
  So that I can monitor service availability

  Scenario: Check API is running
    When I request the health endpoint
    Then I receive a successful response
    And the status is "ok"
    And the version information is present
