#!/usr/bin/env python 
from __future__ import division
import rosbag
from std_msgs.msg import Int32, String
import rosbag
import numpy
import math
import tf
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray
import rospy
from geometry_msgs.msg import Twist,Point
import os

landmark_x =[125,125,125,425,425,425]
landmark_y =[525,325,125,125,325,525]

def minAngle(source,dest):
	a = dest - source
	a = (a + math.pi) % (2*math.pi) - math.pi
	return a


def gaussianPdf(x, mean, var):
    pi = 3.1415926
    denom = (2*pi*var)**.5
    num = math.exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom


def publishToRviz(result):

	topic = 'visualization_marker'
	publisher = rospy.Publisher(topic, Marker,queue_size=100)
	#line strip marker
	line_strip = Marker()
	line_strip.header.frame_id = "/base_link"
	line_strip.header.stamp = rospy.Time.now()
	line_strip.action = Marker.ADD
	line_strip.lifetime = rospy.Time(0)
	line_strip.scale.x = 0.1;
	line_strip.scale.y = 0.1;
	line_strip.scale.z = 0.1;
	line_strip.color.a = 1.0; 
	line_strip.color.r = 0.0;
	line_strip.color.g = 1.0;
	line_strip.color.b = 0.0;
	line_strip.ns = "pts_line"
	line_strip.id = 0
	line_strip.type = Marker.LINE_STRIP
	points_tag = Marker()
	points_tag.header.frame_id = "/base_link"
	points_tag.action = Marker.ADD
	points_tag.header.stamp = rospy.Time.now()
	points_tag.lifetime = rospy.Time(0)
	points_tag.scale.x = 0.1;
	points_tag.scale.y = 0.1;
	points_tag.scale.z = 0.1;
	points_tag.color.a = 1.0; 
	points_tag.color.r = 1.0;
	points_tag.color.g = 0.0;
	points_tag.color.b = 0.0;
	points_tag.ns = "pts_line"
	points_tag.id = 1
	points_tag.type = Marker.POINTS
	p1 = Point()
	p1.x = 1.25
	p1.y = 5.25
	points_tag.points.append(p1)
	p1 = Point()
	p1.x = 1.25
	p1.y = 3.25
	points_tag.points.append(p1)
	p1 = Point()
	p1.x = 1.25
	p1.y = 1.25
	points_tag.points.append(p1)
	p1 = Point()
	p1.x = 4.25
	p1.y = 1.25
	points_tag.points.append(p1)
	p1 = Point()
	p1.x = 4.25
	p1.y = 3.25
	points_tag.points.append(p1)
	p1 = Point()
	p1.x = 4.25
	p1.y = 5.25
	points_tag.points.append(p1)	
	result_length = len(result)
	i=0
	while i<result_length:
		p = Point()
		p.x = result[i]
		i=i+1
		p.y = result[i]
		i=i+1
		line_strip.points.append(p)
	publisher.publish(points_tag)
        publisher.publish(line_strip)


def startPoint():

	bag = rosbag.Bag(os.path.join(os.path.abspath(os.path.dirname(__file__)),
	                              "../grid.bag"))

	#7m*7m grid, 20cm*20cm cell size, considering 10 as discretisation

	d_angle = math.pi/18
	no_dimensions=36

	#initial_pose_third= (200.52/d_angle)
	initial_pose_third= 20
	initial_pose_x=11
	initial_pose_y=27

	grid = numpy.zeros((35,35,no_dimensions))
	new_prob = numpy.zeros((35,35,no_dimensions))
	obs =numpy.zeros((35,35,no_dimensions))

	#Probability of the first cell is initially 1 and the others 0
	grid[initial_pose_x,initial_pose_y,initial_pose_third] =1

	landmark_x =[125,125,125,425,425,425]
	landmark_y =[525,325,125,125,325,525]

	initial_x = (11*20+10)/100
	initial_y= (27*20+10)/100
	result =[initial_x,initial_y]
	temp=0.0
	track=0
	for topic, msg, t in bag.read_messages(topics=['Movements', 'Observations']):

		if topic == 'Movements':
			Motion = msg
			for i in range(0,35):
				for j in range(0,35):
					for k in range(0,no_dimensions):		
					#calculate center position of the cell	
						position_x = 20*i+10
						position_y = 20*j+10			
					
						if(grid[i][j][k]<0.1):
							continue						
						for k1 in range(0,35):
							for k2 in range(0,35):
								for k3 in range(0,no_dimensions):
								#center of this cell						
									if((k1==i) and k2==j):
										continue
									position_x_other = 20*k1+10
									position_y_other = 20*k2+10

									#required translation
									req_translation = numpy.sqrt(numpy.square((position_x -position_x_other)) + numpy.square	((position_y-position_y_other)))

									act_translation = Motion.translation*100
									diff_translation = req_translation-act_translation
								
									probability_translation = gaussianPdf(diff_translation,0,10)

									slope = (math.atan2((position_y_other-position_y), (position_x_other -position_x)))
									#Converting from -180:180 to 0:360 
									if(slope<0):
	#									slope=360+slope
										slope=(2*math.pi)+slope
									req_rot1 = minAngle(d_angle*(k),slope)
									req_rot2 = minAngle(slope,d_angle*(k3))

									#required rotation1 and rotation2				
							
									quaternion = (Motion.rotation1.x,
		Motion.rotation1.y,Motion.rotation1.z,Motion.rotation1.w)
									euler = tf.transformations.euler_from_quaternion(quaternion)

									#act_rot1=math.degrees(euler[2])
									act_rot1=euler[2]
							
									quaternion2 = (Motion.rotation2.x,
		Motion.rotation2.y,Motion.rotation2.z,Motion.rotation2.w)
									euler2 = tf.transformations.euler_from_quaternion(quaternion2)

	#								act_rot2=math.degrees(euler2[2])
									act_rot2=euler2[2]

									diff_rot1 = act_rot1-req_rot1
									diff_rot2 = act_rot2-req_rot2
								
									#difference in rotation1

									probability_rot1 = gaussianPdf(diff_rot1,0,d_angle/2)							

									#difference in rotation2
														
									probabilty_rot2 =gaussianPdf(diff_rot2,0,d_angle/2)							

									prob_inter = probability_translation*probability_rot1*probabilty_rot2
									new_prob[k1][k2][k3] =new_prob[k1][k2][k3]+(grid[i][j][k]*prob_inter)

			grid = new_prob

	
		if topic == 'Observations':
			Observation = msg
			for m in range(0,35):
				for n in range(0,35):
					for p in range(0,no_dimensions):				
						tag_no = Observation.tagNum
						obs_x = landmark_x[tag_no]
						obs_y = landmark_y[tag_no]
						my_pos_x = 20*m+10
						my_pos_y = 20*n+10

						req_range = math.sqrt((my_pos_x -obs_x)**2 + (my_pos_y-obs_y)**2)					

						act_range=(Observation.range)*100
						diff= act_range-req_range

						prob_range=gaussianPdf(diff,0,10)
				
						q2 = (Observation.bearing.x,
		Observation.bearing.y,Observation.bearing.z,Observation.bearing.w)
						e2 = tf.transformations.euler_from_quaternion(q2)
		#				act_bearing = math.degrees(e2[2])
						act_bearing = e2[2]
				
						slope1 = math.atan2((obs_y - my_pos_y), (obs_x -my_pos_x))
						#slope1 = math.atan2(( 525 -10), (125-10))

						#Converting from -180:180 to 0:360
						if(slope1<0):
							slope1=(2*math.pi)+slope1
								
						req_rot1 = minAngle(d_angle*(p),slope1)

						diff_bearing = act_bearing-req_rot1
						prob_bearing = gaussianPdf(diff_bearing,0,d_angle/2)			
						grid[m][n][p]= grid[m][n][p]*prob_range*prob_bearing
				
			grid = grid/numpy.sum(grid)
			max_prob =numpy.amax(grid)

			i1,j1,k1=numpy.unravel_index(numpy.argmax(grid),numpy.shape(grid))
			next_x= (i1*20 +10)/100
			next_y=	(j1*20+10)/100
			result_next=[next_x,next_y]
			result.extend(result_next)
			publishToRviz(result)
	bag.close()


if __name__ == '__main__':
	rospy.init_node('myRobot')
	startPoint()


