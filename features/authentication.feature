@auth
Feature: Demo authentication
  Restful Booker publishes a demo account, admin / password123.
  A valid login returns a token. Invalid logins still respond with HTTP 200
  and a reason of "Bad credentials", and they do not return a token.
  The examples cell "(none)" means an empty string.

  @smoke
  Scenario: The published demo account returns a token
    When I authenticate as "admin" with password "password123"
    Then the response status is 200
    And the response contains an auth token

  @regression
  Scenario Outline: Invalid credentials do not return a token
    When I authenticate as "<username>" with password "<password>"
    Then the response status is 200
    And the response explains that the credentials are bad

    Examples:
      | username | password    |
      | admin    | wrong-pass  |
      | nobody   | password123 |
      | (none)   | (none)      |
