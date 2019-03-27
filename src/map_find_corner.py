#!/usr/bin/env python
import time
from nav_msgs.msg import OccupancyGrid
import rospy 
from utility import *

class MAP_FIND_CORNER():
    def __init__(self):
        pass 

    def init_map_find_corner(self):
        '''
        Given GV.map_ori , init GV.map_find_corner
        '''
        GV.map_find_corner = []
        for value in GV.map_ori.data: # Init map_find_corner
            if value == 100 : # obstacle
                GV.map_find_corner.append(87)
            elif value == -1 : # unknow
                GV.map_find_corner.append(87)
            else: # Value == 0 # space 
                GV.map_find_corner.append(0)
    
    def get_corner_and_contour(self):
        '''
        analayze map_split and find corner and contour init.
        corner : 100 
        contour : 50 
        obstacle : 87 
        '''
        width = GV.width

        # --- Find coner ------#
        for ori_map_pixel in range(len(GV.map_ori.data)):
            if GV.map_ori.data[ori_map_pixel] != 0: # in obstacle 
                pass 
            else: # space
                neighbor_list =  neighbor_value(ori_map_pixel)
                # ----- Boundary check ------# 
                if len(neighbor_list) < 8:
                    print ("Boundary")
                    #self.map_split.append(0)
                    continue

                coner_1 = [100 ,100 ,100, 
                           100 ,     '*',
                           100 ,'*' ,'*']
                coner_2 = [100 ,100 ,100,
                           '*' ,     100,
                           '*' ,'*' ,100]
                coner_3 = [100 ,'*' ,'*', 
                           100 ,     '*',
                           100 ,100 ,100]
                coner_4 = ['*' ,'*' ,100, 
                           '*' ,     100,
                           100 ,100 ,100]
                
                # Inner coner 
                if self.list_compare(neighbor_list, coner_1) or self.list_compare(neighbor_list, coner_2) or self.list_compare(neighbor_list, coner_3) or self.list_compare(neighbor_list, coner_4):
                    print ("Inner Coner !!")
                    GV.map_find_corner[ori_map_pixel] = 100 
                    #(x,y) = self.idx2XY(ori_map_pixel)
                    #self.set_point(x,y,255,255,0, size = 0.1)
                    continue
                
                coner_5 = [100 ,0   ,'*', 
                           0   ,     '*',
                           '*' ,'*' ,'*']
                coner_6 = ['*' ,0   ,100,
                           '*' ,     0,
                           '*' ,'*' ,'*']
                coner_7 = ['*' ,'*' ,'*',
                           0   ,     '*',
                           100 , 0  ,'*']
                coner_8 = ['*' ,'*' ,'*', 
                           '*' ,      0,
                           '*' ,0   ,100]
                
                coner_9 = ['*' ,100   ,0,
                           100 ,       0,
                           0   ,0     ,0]
                coner_10 = [0  ,100 ,'*', 
                            0  ,     100,
                            0  ,0   ,0  ]
                coner_11 = [0  ,0   ,  0, 
                            100,       0,
                            '*',100   ,0]
                coner_12 = [0  ,0     ,0,
                            0  ,     100,
                            0  ,100 ,'*']
                
                if ((self.list_compare(neighbor_list, coner_5) and self.list_compare(neighbor_value(ori_map_pixel- 1 + width), coner_9)) or 
                    (self.list_compare(neighbor_list, coner_6) and self.list_compare(neighbor_value(ori_map_pixel+ 1 + width), coner_10)) or 
                    (self.list_compare(neighbor_list, coner_7) and self.list_compare(neighbor_value(ori_map_pixel- 1 - width), coner_11)) or 
                    (self.list_compare(neighbor_list, coner_8) and self.list_compare(neighbor_value(ori_map_pixel+ 1 - width), coner_12))):
                    print ("Outer Coner !!")
                    GV.map_find_corner[ori_map_pixel] = 100 
                    #(x,y) = self.idx2XY(ori_map_pixel)
                    #self.set_point(x,y,0,255,255, size = 0.1)
                    continue
                
                is_break = False 
                for value in neighbor_list: 
                    if value == 100:# This is edge
                        GV.map_find_corner[ori_map_pixel] = 50
                        #(x,y) = self.idx2XY(ori_map_pixel)
                        #self.set_point(x,y,255,0,0, size = 0.05)
                        is_break = True 
                        break
                if is_break: 
                    continue
                # self.map_split.append(0)
        #--- End finding coner and edge -----# 
    
    def get_aux_corner(self):
        '''
        Use nature corner to create aux corner on map, to make map_split easier.
        refer on map_split 
        Output: 
            aux_corner_list = [idx1, idx2, idx3, .... ]
        '''
        aux_corner_list = []
        for pixel_idx in range(len(GV.map_find_corner)):
            if GV.map_find_corner[pixel_idx] == 100 : # natual coner
                close_list = [] # Already go through
                open_list = [pixel_idx]  # idx that need to be explore
                discover_coner_list = [pixel_idx] # Finally become [coner_start, coner_1 , coner_2]
                while len(discover_coner_list) < 3 : # Exit when there is nothing to explore 
                    x = open_list.pop() # FILO
                    close_list.append(x)
                    
                    neighbor_list = neighbor_idx(x)

                    # Discover coner check 
                    is_discover_new_coner = False 
                    for y in neighbor_list:
                        if GV.map_find_corner[y] == 100 and (y not in discover_coner_list):# It's a new coner !!
                            is_discover_new_coner = True 
                            discover_coner_list.append(y)
                    
                    if not is_discover_new_coner: 
                        for y in neighbor_list:
                            if GV.map_find_corner[y] == 50:
                                if (y not in close_list) and (y not in open_list): # Not explore before, a totally new contour
                                    open_list.append(y)
                # discover_coner_list.pop(0)
                print ("============================")
                print("discover_coner_list : " + str(discover_coner_list))
                
                for i in self.extend_slope(discover_coner_list):
                    print (str(i))
                    aux_corner_list.append(i)
        return aux_corner_list
    
    def list_compare(self, a , b ): 
        '''
        Note that a, b list should have same len
        support wildcard '*'

        retrun False : not same list
        return True : same list
        '''
        for i in range(len(a)):
            if a[i] == '*' or b[i] == '*' : 
                continue
            else: 
                if a[i] == b[i] : 
                    continue
                else: 
                    return False 
        return True  
    
    def extend_slope (self,discover_coner_list):
        '''
        Given nature corner which are neighbor, calculate aux corner at the other direction.
        Input : 
            discover_coner_list = [corner_ori , corner_1 , corner_2] (idx) - nature corner
        Output : 
            ans = [aux_corner_1, aux_corner_2] (idx), len is not fix
        '''
        ans = []
        for t in range(2):
            vertex_end = discover_coner_list[0]
            vertex_start = discover_coner_list[t+1]
            (x_end, y_end) = idx2XY(vertex_end)
            (x_start, y_start) = idx2XY(vertex_start)
            
            slope  = get_slope(idx2XY(vertex_start), idx2XY(vertex_end))
            deltax = x_end - x_start
            line_list = bresenham_line((x_end, y_end), slope, sign(deltax) , self.ED_non_space)
            
            last_idx = XY2idx(line_list[-1])
            if GV.map_find_corner[last_idx] == 50:
                ans.append(last_idx)
        return ans 
    
    def ED_non_space (self, (x,y), end_point, times):
        '''
        Meet non-space return True 
        '''
        value = GV.map_find_corner[XY2idx((x,y))]
        if value != 0: 
            return True 
        else: 
            return False 

