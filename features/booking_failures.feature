@negative
Feature: Booking failures
  These scenarios lock the error behavior of the public demo API.
  An unknown id returns 404. A change without a token returns 403.
  A payload missing required fields is not stored. This demo responds
  with HTTP 500 for that case, rather than a validation 400.

  @regression
  Scenario: An unknown booking id is not found
    When I read booking 999999999
    Then the response status is 404

  @smoke
  Scenario Outline: A change without a token is forbidden
    Given a booking exists for "Taylor" "Brooks"
    When I <action> that booking without a token
    Then the response status is 403

    Examples:
      | action           |
      | replace          |
      | partially update |
      | delete           |

  @regression
  Scenario Outline: An incomplete booking payload is not accepted
    When I create a booking with only "<field>" set to "<value>"
    Then the response status is 500
    And the response does not include a booking id

    Examples:
      | field     | value  |
      | firstname | Riley  |
      | lastname  | Morgan |
