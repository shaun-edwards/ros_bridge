Python Adapter for MTConnect C++ Agent
-------

This is a simple adapter library written in Python to support the ROS
robotics integration project. The adapter supports multiple connections,
heartbeats and the following MTConnect data item types:

* Event  - A simple data item that usually contains with either a controlled
           vocabulary like ControllerMode or Execution, or text like Program.

* Sample - A numeric valued data item for values that are continuously changing
           like position, angle, or temperatures

* ThreeDSample - A sample that represents a three dimensional position like
            a path position. The path is represented by a three space list or
            tuple: (1.0, 2.0, 3.0)

* Condition - A condition is a data item that describes the current normal, fault, or
            warning state of a component for a certain type of problem. A warning is
            a situation that may self correct, whereas a fault needs manual intervention.
            Conditions assume a sweep of a set of error codes where the errors will be
            checked each time the adapter polls. This is usually how most PLCs operate
            and there is no specific message to say when an alarm becomes active or
            clears. If there is an alarm messaging mechanism, use the SimpleCondition.
            Conditions rely on a native code to distinguish themselves. Other systems
            can be used, but this is the current assumption of the agent for its
            condition management.

* SimpleCondition - Similar to Condition, except that when the alarm is cleared, use
            the remove method with the code.


Adapter Creation
------

To create an adapter, import the Adapter from the mtconnect_adapter and add
data items. You need to tell it what host and port it should bind to. The default
port is 7878:

    adapter = Adapter(('0.0.0.0', 7878))
    di = Event('event_1')
    adapter.add_data_item(di)
    adapter.start()

This creates an adapter, adds an Event and then starts the adapter. To change
values of the data item, you need to begin gathering data and then complete the
data gathering process to send all the data.

    adapter.begin_gather()
    di.set_value('hello')
    adapter.complete_gather()

Working with conditions are very similar to the events:

    c1 = SimpleCondition('c1')
    adapter.add_data_item(c1)

    ...

Add a fault

    adapter.begin_gather()
    c1.add('fault', 'A fault', '123')
    adapter.complete_gather()

And to clear the condition:

    adapter.begin_gather()
    c1.remove('123')
    adapter.complete_gather()

There are two additional arguments that are options, qualifier and severity.
The qualifier represents extra information like HIGH or LOW and the severity
is a native severity if available.

There are more examples in the simple_adapter.py.

ROS Example
------
There is an example for the ROS turtlesim tutorial that subscribes to the ROS
poses and then sends them to the MTConnect agent as PATH_POSITION data items. 
To run the demo, install the turtlesim and then run the adapter: (this assumes
the python_adapter is cloned under ~/)

Install the turtle sim -- see ros wiki...

    roscore&
    rosrun turtlesim turtlesim_node

There is an example for the ROS turtlesim tutorial that subscribes to the ROS
poses and then sends them to the MTConnect agent as PATH_POSITION data items. 
To run the demo, install the turtlesim and then run the adapter: (this assumes
the python_adapter is cloned under ~/)

    cd ~/python_adapter/examples
    python ros_adapter.py
    
Next, install the MTConnect agent in another directory:

    cd ~
    git clone http://github.com/mtconnect/cppagent.git
    mkdir agent_build
    cd agent_build
    cmake ../cppagent
    make
    
Run the agent:

    cd ~/python_adapter/examples
    ~/agent_build/agent/agent debug
    
Now your done, test the agent:

    curl http://localhost:5000/current
    
You should see an MTConnect streams document with Availabity AVAILABLE and a PathPosition for the Path.

Simulator
------

The simulator directory contains a ruby script to simulate the functionality of a 
cnc with minimal information only required for the Robot control. The simulator
will process the steps required by the CNC assuming there is a robot that can accept
material related requests. The states will be similar to the states in the 
Bar Feeder project but adapted for to mimic a CNC cell. This technique can be 
used to simulate other MTConnect related devices as well.

The simulator acts as both an agent and an adapter monitoring an external device and
taking actions based on the state and commands. A commandline is also provided to 
allow for actions to be sent that are not initiated by an external device.

Running CNC Simulator
------

The CNC simulator requires ruby 1.9.x and the statemachine gem. Install
ruby and the type

    gem install statemachine

Once you have installed the ruby gem you can use a pre-compiled agent with
the agent.cfg file and the BothDevices.xml to represent a CNC and a robot.
There is a robot response file which just goes through a series of pre-canned
actions and will drive some states on the simulator.

To run the CNC simulator, cd to the simulator directory and start the agent
(assuming it is in the same simulator directory):

    ./agent debug

Next start the CNC simulator:

    ruby cnc_simulator.rb

You will need to type the following commands to enable the cnc, the first puts
it in automatic mode and the second enables the link:

    auto
    enable

Next you will need to start the robot sim:

    ruby robot.rb

Within five seconds give the following command to the CNC:

    run

This process will be made simplier as the CNC becomes more complete. This is the
first step to a fully functioning sim.

License
------
Copyright 2012, System Insights, Inc.
All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

External Licenses
-------

We have included the scanner.py module Copyright (c) 2011, Mark Watkinson.
Additional licensing and copyright information are in the file: src/scanner.py.