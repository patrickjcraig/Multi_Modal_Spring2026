import pandas as pd
import numpy as np

# miscellaneous helper functions to simplify code inside class
def pcd_to_df(pcd): # helper function for converting pcds to df
    points = np.asarray(pcd.points)
    df = pd.DataFrame(points, columns=['X','Y','Z'])
    return df

def tf_to_df(result): # helper function to store the transformation matrix of result data
    return pd.DataFrame(result.transformation, columns=['C1','C2','C3','C4'], index=['R1','R2','R3','R4'])

def reg_to_df(result): # helper function to store the metadata of result data
    return pd.DataFrame({'Fitness':[result.fitness], 'Inlier RMSE':[result.inlier_rmse]})