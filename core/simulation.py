"""
Motor de simulación numérica para el gemelo digital.
"""

import math
import numpy as np

from core.robot import RobotModel


def generate_multi_point_trajectory(waypoints: list[np.ndarray], duration_sec: float, fps: int = 30) -> np.ndarray:
    """
    Genera una trayectoria continua a través de múltiples puntos de paso (waypoints).
    
    Args:
        waypoints: Lista de arrays NumPy, donde cada elemento es un vector q con las variables articulares.
        duration_sec: Duración total de la simulación en segundos.
        fps: Cuadros por segundo para la animación.
        
    Returns:
        Matriz NumPy de tamaño (total_frames, DOF) con la secuencia articular interpolada.
    """
    if len(waypoints) < 2:
        raise ValueError("Se requieren al menos 2 puntos para generar una trayectoria.")
    
    num_segments = len(waypoints) - 1
    duration_per_seg = duration_sec / num_segments
    frames_per_seg = max(2, int(duration_per_seg * fps))
    
    trajectory_list = []
    for i in range(num_segments):
        seg = np.linspace(waypoints[i], waypoints[i + 1], frames_per_seg)
        # Evitar duplicar el punto límite de unión entre segmentos
        if i > 0:
            seg = seg[1:]
        trajectory_list.append(seg)
        
    return np.vstack(trajectory_list)


def compute_fast_geometry(robot: RobotModel, q_values: np.ndarray) -> np.ndarray:
    """
    Calcula los puntos espaciales (base, codos, orígenes) de un manipulador.
    """
    points = [np.array([0.0, 0.0, 0.0])]
    T_accum = np.eye(4)
    
    for i, joint in enumerate(robot.joints):
        q = q_values[i]
        
        if joint.joint_type.is_revolute:
            theta = math.radians(q)
            d = joint.dh.d
        else:
            theta = math.radians(joint.dh.theta)
            d = q
            
        a = joint.dh.a
        alpha = math.radians(joint.dh.alpha)
        
        # 1. Punto intermedio (codo DH)
        p_intermediate_local = np.array([0, 0, d, 1])
        p_intermediate_global = T_accum @ p_intermediate_local
        points.append(p_intermediate_global[:3])
        
        # 2. Matriz DH local
        ct, st = np.cos(theta), np.sin(theta)
        ca, sa = np.cos(alpha), np.sin(alpha)
        
        T_local = np.array([
            [ct, -st * ca,  st * sa, a * ct],
            [st,  ct * ca, -ct * sa, a * st],
            [ 0,      sa,      ca,    d],
            [ 0,       0,       0,    1]
        ])
        
        T_accum = T_accum @ T_local
        points.append(T_accum[:3, 3])
        
    return np.array(points)


def precompute_animation_frames(robot: RobotModel, trajectory_q: np.ndarray) -> list[np.ndarray]:
    """
    Precalcula la geometría espacial de todos los cuadros de la trayectoria.
    """
    return [compute_fast_geometry(robot, q_vals) for q_vals in trajectory_q]