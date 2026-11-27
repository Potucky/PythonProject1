@lifecycle
Feature: Booking lifecycle
  End-to-end guest booking on the public Restful Booker API.
  Creating and reading a booking does not need a token.
  Replacing, patching, and deleting do. A successful delete returns 201.

  Background:
    Given the booking service is healthy

  @smoke
  Scenario: Create a booking and read it back
    When I create a booking for "Riley" "Morgan" priced at 150
    Then the response status is 200
    And the response includes a booking id
    When I read that booking
    Then the response status is 200
    And the booking name is "Riley" "Morgan"
    And the booking total price is 150

  @smoke
  Scenario: Replace a booking with an auth token
    Given I am authenticated with the demo account
    And a booking exists for "Jamie" "Rivera"
    When I replace that booking with first name "Jordan"
    Then the response status is 200
    And the booking name is "Jordan" "Rivera"
    When I read that booking
    Then the booking name is "Jordan" "Rivera"

  @regression
  Scenario: Patch a booking last name
    Given I am authenticated with the demo account
    And a booking exists for "Alex" "Chen"
    When I partially update that booking last name to "Nguyen"
    Then the response status is 200
    And the booking name is "Alex" "Nguyen"
    When I read that booking
    Then the booking name is "Alex" "Nguyen"

  @regression
  Scenario: Delete a booking
    Given I am authenticated with the demo account
    And a booking exists for "Sam" "Patel"
    When I delete that booking
    Then the response status is 201
    When I read that booking
    Then the response status is 404
