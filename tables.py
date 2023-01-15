#dict keys in format: piece state, future piece state
    #NOTE: the y values are actually negative to what they should be (this is accounted for)
WALL_KICK_TABLE_NORMAL = {
    "01" : ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    "10" : ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),

    "12" : ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    "21" : ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),

    "23" : ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    "32" : ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),

    "30" : ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)), 
    "03" : ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)), 
}

I_KICK_TABLE = {
    "01" : ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),  
    "10" : ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),  

    "12" : ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)), 
    "21" : ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),

    "23" : ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
    "32" : ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),

    "30" : ((0, 0), (1, 0), (-2 ,0), (1, -2), (-2 ,1)),
    "03" : ((0, 0), (-1, 0), (2 ,0), (-1, 2), (2 ,-1)),
}

FOUR_CORNERS_RULE = ((0,0),(0,2),(2,0),(2,2))

SCORE_CHART = {
    0 : 0,
    1 : 40,
    2 : 100,
    3 : 300,
    4 : 1200,
}