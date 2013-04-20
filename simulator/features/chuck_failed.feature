# Copyright 2012, System Insights, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

Feature: Machine Tool Chuck Fails
  The robot asks the machine tool to open it's chuck
  but the chuck fails

  Background: Machine Tool and Robot are operational
    Given Devices are in initial state

  Scenario: Cnc Can't Close It's Chuck
    Given robot MaterialLoad becomes Active
    Then material load state should be processing

    When robot CloseChuck becomes Active
    Then cnc CloseChuck should be Active
    And cnc ChuckState becomes Unlatched

    When cnc CloseChuck becomes Failure
    Then close chuck state should be fail
    And cnc CloseChuck should be Fail
    And cnc ChuckState should be Unlatched
    And cnc should have fault
    And machine state should be fault
    And cnc fault should have code "Cnc::CloseChuck"

  Scenario: Cnc Can't Close Chuck and then Recovers
    Given robot MaterialLoad becomes Active
    Then material load state should be processing

    When robot CloseChuck becomes Active
    Then cnc CloseChuck should be Active
    And cnc ChuckState becomes Unlatched

    When cnc CloseChuck becomes Failure
    And close chuck state should be fail
    And robot CloseChuck becomes Fail
    Then cnc CloseChuck should be Not_Ready

    When robot CloseChuck becomes Ready
    Then cnc CloseChuck should be Not_Ready
    And machine state should be fault

    When faults are cleared
    And cnc is reset
    Then machine state should be loading
    And cnc CloseChuck should be READY
