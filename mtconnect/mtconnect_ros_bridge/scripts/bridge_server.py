#! /usr/bin/env python

"""
   Copyright 2013 Southwest Research Institute
 
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
 
     http://www.apache.org/licenses/LICENSE-2.0
 
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
   """

# Import standard Python modules
import sys
import os
import operator
import thread
import re
import time
from importlib import import_module
from httplib import HTTPConnection
from xml.etree import ElementTree

# Import custom Python module to read config file
import read_config_file

# Import custom Python modules for MTConnect Adapter interface
path, file = os.path.split(__file__)
sys.path.append(os.path.realpath(path) + '/src')
from data_item import Event, SimpleCondition, Sample, ThreeDSample
from mtconnect_adapter import Adapter
from long_pull import LongPull

# Import ROS Python modules
import roslib
import rospy
import actionlib

class GenericActionServer():
    def __init__(self):
        # Initialize ROS generic client node
        rospy.init_node('ActionServer')
        
        # Setup MTConnect to ROS Conversion
        self.config = read_config_file.obtain_dataMap()
        
        # Setup MTConnect Adapter for robot status data items
        self.adapter = Adapter(('0.0.0.0', self.config['Port']))
        self.ns = dict(m = 'urn:mtconnect.org:MTConnectStreams:1.2')
        
        # Create empty lists for actions, message type handles, etc.
        self.lib_manifests = []
        self.type_handle = None
        self.action_list = {}
        self.action_goals = {}
        self.action_conv = []
        self.namespace = None
        self.xml_goal = None
        self.di_dict = {} # XML data item dictionary to store MTConnect Adapter Events
        
        # Setup action client data per the config file
        self.setup_topic_data()
        
        # Add data items to the MTConnect Adapter - must be unique data items
        self.add_agent()
        
        # Start the adapter
        rospy.loginfo('Start the Robot Link adapter')
        self.adapter.start()
        
        # Establish XML connection, read in current XML
        self.conn = HTTPConnection('localhost', self.config['localhost'])
        #response = self.xml_get_response("/cnc/current")
        #cnc_body = response.read()
        
        # Parse the XML and determine the current sequence and XML Event elements
        #seq, elements = self.xml_components(cnc_body)
        
        # Start a streaming XML connection
        #response = self.xml_get_response("/cnc/sample?interval=1000&count=1000&from=" + seq)
        
        # Create class lock
        #self.lock = thread.allocate_lock()

        # Create XML polling thread
        #lp = LongPull(response)
        #lp.long_pull(self.xml_callback) # Runs until user interrupts
        
        # Create a dictionary of _results to return upon action success
        self._resultDict = {}
        
        # Create a dictionary of action servers
        self._as = {}
        
        # Create a dictionary of server names
        self.server_name = {}
        
        # Iterate through actions and create action call-backs and action result class instances
        for ns, action in self.config.items():
            if ns != 'localhost' and ns != 'Port': # Only one ROS namespace in config by design
                for request in action.keys():
                    di_conv = self.split_event(request)
                    self.server_name[di_conv] = request
                    
                    # Create a dictionary of result class instances
                    request_class = getattr(self.type_handle, request + 'Result')
                    self._resultDict[request] = request_class()
                    
                    # Create instance of the action class
                    action_class = getattr(self.type_handle, request + 'Action')
                    
                    # Create action server for requested action
                    self._as[request] = actionlib.SimpleActionServer(request + 'Client', action_class, self.execute_cb, False)
                    
                    # Start the action server
                    self._as[request].start()
        
    
    def add_agent(self):
        # For each data item in config file, add Event and data item
        for xml_tag in self.action_list:
            data_item = self.split_event(xml_tag)
            self.di_dict[data_item] = Event(data_item)
            self.adapter.add_data_item(self.di_dict[data_item])
            
            rospy.loginfo('data_item --> %s' % xml_tag)
        
        # Set initial states for robot actions
        self.adapter.begin_gather()
        for data_item, event in self.di_dict.items():
            event.set_value('READY')
        self.adapter.complete_gather()

        return
    
    def split_event(self, xml_tag):
        tokens = re.findall(r'([A-Z][a-z]*)', xml_tag)
        tokenlist = [val.lower() for val in tokens]
        data_item = tokenlist[0] + '_' + tokenlist[1]
        return data_item
                
    def setup_topic_data(self):
        """This function captures the topic namespace, type, action goals,
        and action state conversion from ROS to MTConnect as required for
        the ROS action client.  This task completed for each topic specified
        in the configuration file.
        
        This function then performs a relative import of the topic
        via the getattr(import_module) function.  Data is stored in the
        following class attributes:
        
            self.lib_manifests --> used to track which manifests have been loaded
            self.type_handle   --> used for ROS SimpleActionClient, stores namespace with action messages
            self.action_list   --> used for ROS SimpleActionClient, stores CNC action request strings
            self.action_goals  --> data structure for message class instances of the topic type
        """
        
        for namespace, action in self.config.items():
            if namespace != 'localhost' and namespace != 'Port': # Only one ROS namespace in config by design
                # Load package manifest if unique
                if namespace not in self.lib_manifests:
                    roslib.load_manifest(namespace)
                    self.lib_manifests.append(namespace)

                # Import module
                rospy.loginfo('Importing --> ' + namespace + '.msg')
                self.type_handle = import_module(namespace + '.msg')
                
                # Capture namespace for action client
                self.namespace = namespace
                
                for action_req in action.keys():
                    # Capture action name for action client callback reference
                    self.action_list[action_req] = action_req
                    
                    # Capture ROS Action parameters
                    goal_key = self.config[namespace][action_req].keys()[0]
                    self.action_goals[action_req] = self.config[namespace][action_req][goal_key].keys()
                    
                    # Capture ROS to MTConnect state conversion dictionary
                    #self.action_conv[action_req] = self.config[namespace][action_req]['conversion']
        return
    
    def xml_get_response(self, req):
        self.conn.request("GET", req)
        response = self.conn.getresponse()
        if response.status != 200:
            rospy.loginfo("Request failed: %s - %d" % (response.reason, response.status))
            sys.exit(0)
        else:
            rospy.loginfo('Request --> %s, Status --> %s' % (response.reason, response.status))
        return response
    
    def xml_components(self, xml):
        """ Find all elements in the updated xml.
        root.find requires namespaces to be a dictionary.
        Return sequence and elements to process ROS msgs.
        """
        root = ElementTree.fromstring(xml)
        header = root.find('.//m:Header', namespaces=self.ns)
        nextSeq = header.attrib['nextSequence']
       
        elements = []

        for action in self.action_list:
            find_action = root.findall('.//m:' + action, namespaces=self.ns)
            if find_action: # Element list is not empty
                elements.append(find_action[0])
        return nextSeq, elements

    def execute_cb(self, goal):
        # If goal is OpenDoor, use the goal defined in the message as your key, access it as goal.__slots__[0]
        action = goal.__slots__[0]
        # Empty function -- assumes action was successful
        rospy.loginfo('In %s Callback -- determining action request result.' % self.server_name[action])
        
        # Submit goal value to MTConnect via agent (i.e. goal.open_door = 'ACTIVE')
        rospy.loginfo("Changing %s to 'ACTIVE'" % self.server_name[action])
        self.adapter.begin_gather()
        self.di_dict[action].set_value('ACTIVE')
        self.adapter.complete_gather()
        robot_hold = 0 # Used to make sure you only change robot state once after 'COMPLETE' received from CNC
        
        # While loop to poll CNC XML until READY is received for OpenDoor
        dwell = True
        while dwell == True: # Replace text with dynamic reference to yaml file
            # While polling monitor CNC response for ACTIVE,
            # if so, inform Action Client that goal has been accepted -- use 'set accepted' method
            # remain in while loop
            
            # Poll CNC XML for goal state
            response = self.xml_get_response("/cnc/current")
            cnc_body = response.read()
            
            # Parse the XML and determine the current sequence and XML Event elements
            root = ElementTree.fromstring(cnc_body)
            element = root.findall('.//m:' + self.server_name[action], namespaces=self.ns)[0]
            
            if element.text == 'ACTIVE':
                # Set accepted back to action client
                pass
            
            # While polling monitor CNC response for COMPLETE, submit READY handshake
            elif element.text == 'COMPLETE' and robot_hold == 0: # Need to check robot XML as well
                rospy.loginfo("Changing %s to 'READY'" % self.server_name[action])
                self.adapter.begin_gather()
                self.di_dict[action].set_value('READY')
                self.adapter.complete_gather()
                robot_hold = 1
            
            elif element.text == 'READY' and robot_hold == 1:
                dwell = False
            
            
        # When response is READY, set server result and communicate as below:
         
        # Extract action attribute
        result_attribute = self._resultDict[self.server_name[action]].__slots__[0]
        
        # Create code object to set the attribute per the ROS to MTConnect conversion
        #setattr(self._resultDict[self.server_name[action]], result_attribute, self.config[self.server_name[action]][tbd])
        setattr(self._resultDict[self.server_name[action]], result_attribute, 'READY')
        
        # Indicate a successful action
        self._as[self.server_name[action]].set_succeeded(self._resultDict[self.server_name[action]])
        rospy.loginfo('In %s Callback -- action succeeded.' % self.server_name[action])
        return

if __name__ == '__main__':
    try:
        rospy.loginfo('Started Generic Action Server')
        robot_action = GenericActionServer()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo('program interrupted before completion')