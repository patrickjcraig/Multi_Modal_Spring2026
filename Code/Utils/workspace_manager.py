# file for saving and loading workspace for app (saves parameters, settings, etc)
# IMPORTANT: THIS DOES NOT SAVE THE SCAN ITSELF AS OPEN3D RUNS ON C++
import pickle


def save_workspace(filepath, workspace_data):
    """
    Save workspace data to a file using pickle.
    
    Args:
        filepath (str): Path to save file
        workspace_data (dict): Dictionary containing workspace state
    """
    with open(filepath, 'wb') as f:
        pickle.dump(workspace_data, f)


def load_workspace(filepath):
    """
    Load workspace data from a pickle file.
    
    Args:
        filepath (str): Path to workspace file
        
    Returns:
        dict: Loaded workspace data
    """
    with open(filepath, 'rb') as f:
        return pickle.load(f)