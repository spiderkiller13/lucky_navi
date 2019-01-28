#!/usr/bin/env python
import time
import math
from nav_msgs.msg import OccupancyGrid # Global map 
from geometry_msgs.msg import PoseArray, PoseStamped, Pose2D, Pose, Twist   # Global path 
import rospy 
import sys 
from visualization_msgs.msg import Marker, MarkerArray # Debug drawing 
import tf2_ros 
from tf import transformations

#----- Load paramters -----# 
# foot_print = [[-0.57, 0.36],[0.57, 0.36],[0.57, -0.36],[-0.57, -0.36]]
p1 = 1
p2 = 1/0.375 
Vel_limit = 0.7 # Should be in class, modified dynamic.
IS_ENABLE_MOVE_BACKWORD = True 




# LVP = LINEAR_VELOCITY_PLANNER()
pub_marker = rospy.Publisher('markers', MarkerArray,queue_size = 1,  latch=False )

class LINEAR_VELOCITY_PLANNER():
    def __init__(self):
        #----- Current Pose ------# 
        self.current_position = PoseStamped()
        # ---- Current Goal ------# 
        self.goal = PoseStamped()
        self.goal_mode = "waypoint" # 
        # ---- State Machine -----#
        self.state = "stand_by" # "abort", "timeout" , "moving"
        #------- #
        self.markerArray = MarkerArray()
        #----- Publisher ------# 
        self.pub_cmd_vel = rospy.Publisher('/cmd_vel', Twist ,queue_size = 10,  latch=False)
        self.cmd_vel = Twist()
        #----- Counting Star ------# 
        self.t_start_moving = None 

    def reset (self):
        '''
        Clean Current Task , and reset to init.
        '''
        # ---- Current Goal ------# 
        self.goal = PoseStamped()
        # ---- State Machine -----#
        self.state = "stand_by" # "abort", "timeout" , "moving"
        #------- #
        self.markerArray = MarkerArray()
        #----- Counting Star ------# 
        self.t_start_moving = None 

    def clean_screen (self):
        #------- clean screen -------#
        marker = Marker()
        marker.header.frame_id = "/map"
        marker.action = marker.DELETEALL
        self.markerArray.markers.append(marker)
        pub_marker.publish(self.markerArray)

        #------- Debug draw -------# 
        self.markerArray = MarkerArray()

    def move_base_simple_goal_CB(self, goal):
        rospy.loginfo ("Target : " + str(goal))
        self.goal = goal # TODO Check Valid Goal, or the goal is already reached.
        self.state = "moving"
        # TODO Do something.
        #self.reset()
        #self.navi_goal = self.XY2idx((navi_goal.pose.position.x, navi_goal.pose.position.y))
        self.t_start_moving  = time.time()
    
    def current_position_CB(self, current_position):
        # print ("Current Position : " + str(current_position))
        self.current_position = current_position

    def sign (self, x):
        if x >= 0: 
            return 1
        else: 
            return -1 
        
    def angle_substitution(self, ang):
        '''
        Make sure  ang is 0 ~ pi/2 or -0 ~ -pi/2 
        '''
        ans = (abs(ang) % (2* math.pi)) * self.sign(ang) # Make sure not ot exceed 360

        if ans > math.pi :
            # return (2* math.pi) - ans 
            ans =  ans - (2* math.pi) # Negative 
        elif ans < -math.pi : 
            ans =  (2* math.pi) + ans # Positive 
        else: 
            pass 
        return ans 


    def iterateOnce (self):
        '''
        Switch Case 
        '''
        if self.state == "stand_by":
            pass
        elif self.state == "reached":
            rospy.loginfo ("[Linear_velocity_planner] time spend: " + str(time.time() - self.t_start_moving))
            self.reset() 

        elif self.state == "moving": 
            #----- Get r , alpha , beta ------# 
            pos_dx = self.goal.pose.position.x - self.current_position.pose.position.x
            pos_dy = self.goal.pose.position.y - self.current_position.pose.position.y
            r = math.sqrt(pos_dx*pos_dx + pos_dy*pos_dy)

            r_yaw = math.atan2(pos_dy, pos_dx)

            cureent_position_yaw = transformations.euler_from_quaternion(self.pose_quaternion_2_list(self.current_position.pose.orientation))[2]
            alpha = self.angle_substitution(cureent_position_yaw - r_yaw)

            # ------- Check Go Farword or Backword --------#
            linear_direction = 1 
            if IS_ENABLE_MOVE_BACKWORD: 
                if abs(alpha) > math.pi/2:
                    rospy.loginfo("Decide to go BackWord.")
                    cureent_position_yaw = self.angle_substitution(cureent_position_yaw + math.pi)
                    alpha = self.angle_substitution(cureent_position_yaw - r_yaw)
                    linear_direction = -1 

            goal_yaw = transformations.euler_from_quaternion(self.pose_quaternion_2_list(self.goal.pose.orientation))[2]
            beta = self.angle_substitution(goal_yaw - r_yaw)
            
            rospy.loginfo ("++++++++++++++++++++++++++")
            rospy.loginfo ("cureent_position_yaw = " + str(cureent_position_yaw))
            rospy.loginfo ("r_yaw = " + str(r_yaw))
            rospy.loginfo ("r = " + str(r))
            rospy.loginfo ("alpha = " + str(alpha))
            rospy.loginfo ("beta = " + str(beta))


            V =  abs(p1*r*math.cos(alpha)) * linear_direction

            if r < 0.05 :
                W = p2*(-beta)
            else: 
                W = p2*(-alpha)

            k = Vel_limit / (abs(V) + abs(W))

            V = V * k
            W = W * k


            #---------------------------------#
            #reached or not 
            if self.goal_mode == "waypoint" and  r < 0.05 :
                V = 0 
                W = 0
                self.state = "reached"
                
            #---------------------------------#
            rospy.loginfo ("V = " + str(V))
            rospy.loginfo ("W = " + str(W))
            self.cmd_vel.linear.x = V 
            self.cmd_vel.angular.z = W
            self.pub_cmd_vel.publish(self.cmd_vel)
        else: 
            pass 
        
    def set_point(self, idx ,r ,g ,b ):
        '''
        Set Point at MarkArray 
        '''
        marker = Marker()
        marker.header.frame_id = "/map"
        marker.id = idx 
        marker.ns = "tiles"
        marker.header.stamp = rospy.get_rostime()
        marker.type = marker.SPHERE
        marker.action = marker.ADD
        marker.scale.x = 0.05
        marker.scale.y = 0.05
        marker.scale.z = 0.05
        marker.color.a = 1.0
        marker.color.r = r/255.0
        marker.color.g = g/255.0
        marker.color.b = b/255.0
        marker.pose.orientation.w = 1.0
        # (marker.pose.position.x , marker.pose.position.y) = self.idx2XY(idx)
        self.markerArray.markers.append(marker)
    
    def pose_quaternion_2_list(self, quaternion):
        """
        This function help transfer the geometry_msgs.msg.PoseStameped 
        into (translation, quaternion) <-- lists
        """
        return [quaternion.x, quaternion.y, quaternion.z, quaternion.w]

#----- Declare Class -----# 
LVP = LINEAR_VELOCITY_PLANNER()

def main(args):
    #----- Init node ------# 
    rospy.init_node('linear_velocity_planner', anonymous=True)
    rospy.Subscriber('/move_base_simple/goal', PoseStamped, LVP.move_base_simple_goal_CB) # TODO for testing 
    rospy.Subscriber('/current_position', PoseStamped, LVP.current_position_CB) 

    r = rospy.Rate(10)#call at 10HZ
    while (not rospy.is_shutdown()):
        '''
        if GC.is_need_pub: 
            pub_global_costmap.publish(GC.global_costmap)
            GC.is_need_pub = False
        if GP.is_need_pub:
            pub_global_path.publish(GP.global_path)
            GP.is_need_pub = False
        '''
        LVP.iterateOnce()
        r.sleep()

if __name__ == '__main__':
    try:
        main(sys.argv)
    except rospy.ROSInterruptException:
        pass

    

